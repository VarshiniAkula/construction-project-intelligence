"""Document ingestion pipeline — runs as BackgroundTask (no Celery needed)."""
import io
import csv
import json
import uuid
import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.services.storage import upload_file, download_file

logger = logging.getLogger(__name__)

# Sync engine for background tasks (asyncio BackgroundTasks run in threadpool)
_sync_engine = None
_SyncSession = None


def _get_sync_session():
    global _sync_engine, _SyncSession
    if _sync_engine is None:
        db_url = settings.DATABASE_URL
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg")
        _sync_engine = create_engine(db_url, pool_pre_ping=True)
        _SyncSession = sessionmaker(bind=_sync_engine)
    return _SyncSession()


def ingest_document(document_id: str):
    """Full ingestion pipeline for a document. Runs synchronously in a thread."""
    session = _get_sync_session()

    try:
        result = session.execute(
            text("SELECT * FROM documents WHERE id = :id"),
            {"id": document_id},
        )
        doc_row = result.mappings().first()
        if not doc_row:
            logger.error(f"Document {document_id} not found")
            return

        project_id = doc_row["project_id"]
        storage_key = doc_row["storage_key"]
        file_type = storage_key.rsplit(".", 1)[-1] if "." in storage_key else "pdf"
        doc_type = doc_row["doc_type"]
        visibility_scope = doc_row["visibility_scope"]
        trade_scope = doc_row["trade_scope"] or ""

        logger.info(f"Starting ingestion for document {document_id} ({file_type})")

        session.execute(
            text("UPDATE documents SET status = 'rendering_pages' WHERE id = :id"),
            {"id": document_id},
        )
        session.commit()

        # Download file
        file_data = download_file(storage_key)

        # Process based on type
        if file_type == "pdf":
            pages_data = _process_pdf(session, document_id, project_id, file_data)
        elif file_type in ("png", "jpg", "jpeg"):
            pages_data = _process_image(session, document_id, project_id, file_data, file_type)
        elif file_type == "docx":
            pages_data = _process_docx(session, document_id, file_data)
        elif file_type in ("xlsx", "xls"):
            pages_data = _process_xlsx(session, document_id, file_data)
        elif file_type == "csv":
            pages_data = _process_csv(session, document_id, file_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Update page count
        session.execute(
            text("UPDATE documents SET page_count = :count, status = 'chunking' WHERE id = :id"),
            {"count": len(pages_data), "id": document_id},
        )
        session.commit()

        # Chunk
        chunks = _chunk_pages(pages_data, doc_type)
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        # Embed and store
        session.execute(
            text("UPDATE documents SET status = 'embedding' WHERE id = :id"),
            {"id": document_id},
        )
        session.commit()

        if chunks:
            _embed_and_store(session, document_id, project_id, chunks, visibility_scope, trade_scope, doc_type)

        session.execute(
            text("UPDATE documents SET status = 'ready' WHERE id = :id"),
            {"id": document_id},
        )
        session.commit()
        logger.info(f"Document {document_id} ingestion complete")

    except Exception as e:
        logger.error(f"Ingestion failed for {document_id}: {e}", exc_info=True)
        try:
            session.execute(
                text("UPDATE documents SET status = 'error', processing_error = :err WHERE id = :id"),
                {"err": str(e)[:1000], "id": document_id},
            )
            session.commit()
        except Exception:
            session.rollback()
    finally:
        session.close()


def _process_pdf(session, document_id: str, project_id: str, file_data: bytes) -> list[dict]:
    import fitz

    doc = fitz.open(stream=file_data, filetype="pdf")
    pages_data = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        raw_text = page.get_text("text")

        # Render page image
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")

        image_key = f"projects/{project_id}/documents/{document_id}/pages/{page_num + 1}.png"
        upload_file(image_key, img_bytes, content_type="image/png")

        page_summary = raw_text[:500] if raw_text else ""
        cleaned_text = raw_text.strip()

        page_id = str(uuid.uuid4())
        session.execute(
            text("""INSERT INTO document_pages
                (id, document_id, page_number, raw_text, cleaned_text, page_summary,
                 image_storage_key, extracted_json, created_at, updated_at)
                VALUES (:id, :doc_id, :pn, :raw, :cleaned, :summary, :img_key, NULL,
                        NOW(), NOW())"""),
            {
                "id": page_id, "doc_id": document_id, "pn": page_num + 1,
                "raw": raw_text, "cleaned": cleaned_text, "summary": page_summary,
                "img_key": image_key,
            },
        )

        pages_data.append({
            "page_number": page_num + 1,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "summary": page_summary,
        })

    session.commit()
    doc.close()
    return pages_data


def _process_image(session, document_id: str, project_id: str, file_data: bytes, file_type: str) -> list[dict]:
    image_key = f"projects/{project_id}/documents/{document_id}/pages/1.png"
    upload_file(image_key, file_data, content_type=f"image/{file_type}")

    page_id = str(uuid.uuid4())
    session.execute(
        text("""INSERT INTO document_pages
            (id, document_id, page_number, raw_text, cleaned_text, page_summary,
             image_storage_key, extracted_json, created_at, updated_at)
            VALUES (:id, :doc_id, 1, '', 'Image document', 'Image document', :img_key, NULL, NOW(), NOW())"""),
        {"id": page_id, "doc_id": document_id, "img_key": image_key},
    )
    session.commit()
    return [{"page_number": 1, "raw_text": "", "cleaned_text": "Image document", "summary": "Image document"}]


def _process_docx(session, document_id: str, file_data: bytes) -> list[dict]:
    from docx import Document as DocxDocument

    doc = DocxDocument(io.BytesIO(file_data))
    full_text_parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            full_text_parts.append(para.text)

    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                full_text_parts.append(row_text)

    full_text = "\n".join(full_text_parts)
    pages_data = []
    page_size = 3000
    for i in range(0, max(len(full_text), 1), page_size):
        page_num = (i // page_size) + 1
        page_text = full_text[i:i + page_size]
        if not page_text.strip():
            continue

        page_id = str(uuid.uuid4())
        session.execute(
            text("""INSERT INTO document_pages
                (id, document_id, page_number, raw_text, cleaned_text, page_summary,
                 image_storage_key, extracted_json, created_at, updated_at)
                VALUES (:id, :doc_id, :pn, :raw, :cleaned, :summary, NULL, NULL, NOW(), NOW())"""),
            {
                "id": page_id, "doc_id": document_id, "pn": page_num,
                "raw": page_text, "cleaned": page_text, "summary": page_text[:500],
            },
        )
        pages_data.append({
            "page_number": page_num, "raw_text": page_text,
            "cleaned_text": page_text, "summary": page_text[:500],
        })

    if not pages_data:
        pages_data = [{"page_number": 1, "raw_text": "", "cleaned_text": "Empty document", "summary": "Empty document"}]

    session.commit()
    return pages_data


def _process_xlsx(session, document_id: str, file_data: bytes) -> list[dict]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(file_data), read_only=True, data_only=True)
    pages_data = []
    page_num = 0

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows_text = []

        for row in ws.iter_rows(values_only=True):
            cell_values = [str(c) if c is not None else "" for c in row]
            if not any(v.strip() for v in cell_values):
                continue
            rows_text.append(" | ".join(cell_values))

        if not rows_text:
            continue

        chunk_size = 50
        for i in range(0, len(rows_text), chunk_size):
            page_num += 1
            chunk_rows = rows_text[i:i + chunk_size]
            page_text = f"Sheet: {sheet_name}\n" + "\n".join(chunk_rows)

            page_id = str(uuid.uuid4())
            session.execute(
                text("""INSERT INTO document_pages
                    (id, document_id, page_number, raw_text, cleaned_text, page_summary,
                     image_storage_key, extracted_json, created_at, updated_at)
                    VALUES (:id, :doc_id, :pn, :raw, :cleaned, :summary, NULL, NULL, NOW(), NOW())"""),
                {
                    "id": page_id, "doc_id": document_id, "pn": page_num,
                    "raw": page_text, "cleaned": page_text,
                    "summary": f"Sheet '{sheet_name}' rows {i+1}-{i+len(chunk_rows)}",
                },
            )
            pages_data.append({
                "page_number": page_num, "raw_text": page_text,
                "cleaned_text": page_text,
                "summary": f"Sheet '{sheet_name}' rows {i+1}-{i+len(chunk_rows)}",
            })

    wb.close()
    if not pages_data:
        pages_data = [{"page_number": 1, "raw_text": "", "cleaned_text": "Empty spreadsheet", "summary": "Empty spreadsheet"}]

    session.commit()
    return pages_data


def _process_csv(session, document_id: str, file_data: bytes) -> list[dict]:
    text_content = file_data.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text_content))
    rows_text = [" | ".join(row) for row in reader if any(c.strip() for c in row)]

    pages_data = []
    chunk_size = 50
    for i in range(0, max(len(rows_text), 1), chunk_size):
        page_num = (i // chunk_size) + 1
        chunk_rows = rows_text[i:i + chunk_size]
        page_text = "\n".join(chunk_rows)
        if not page_text.strip():
            continue

        page_id = str(uuid.uuid4())
        session.execute(
            text("""INSERT INTO document_pages
                (id, document_id, page_number, raw_text, cleaned_text, page_summary,
                 image_storage_key, extracted_json, created_at, updated_at)
                VALUES (:id, :doc_id, :pn, :raw, :cleaned, :summary, NULL, NULL, NOW(), NOW())"""),
            {
                "id": page_id, "doc_id": document_id, "pn": page_num,
                "raw": page_text, "cleaned": page_text,
                "summary": f"CSV rows {i+1}-{i+len(chunk_rows)}",
            },
        )
        pages_data.append({
            "page_number": page_num, "raw_text": page_text,
            "cleaned_text": page_text, "summary": f"CSV rows {i+1}-{i+len(chunk_rows)}",
        })

    if not pages_data:
        pages_data = [{"page_number": 1, "raw_text": "", "cleaned_text": "Empty CSV", "summary": "Empty CSV"}]

    session.commit()
    return pages_data


def _chunk_pages(pages_data: list[dict], doc_type: str) -> list[dict]:
    chunks = []

    if doc_type == "drawing":
        for page in pages_data:
            t = page["cleaned_text"] or page["summary"] or ""
            if t.strip():
                chunks.append({"page_number": page["page_number"], "text": t, "chunk_type": "drawing_page"})

    elif doc_type == "specification":
        for page in pages_data:
            t = page["cleaned_text"] or ""
            if not t.strip():
                continue
            import re
            sections = re.split(r'\n(?=\d+\.\d+[\s.])', t)
            for section in sections:
                if section.strip():
                    chunks.append({"page_number": page["page_number"], "text": section, "chunk_type": "spec_section"})

    elif doc_type in ("rfi", "submittal"):
        full_text = "\n\n".join(p["cleaned_text"] or p["summary"] or "" for p in pages_data)
        if full_text.strip():
            chunks.append({"page_number": 1, "text": full_text[:3000], "chunk_type": f"{doc_type}_record"})

    elif doc_type == "daily_report":
        for page in pages_data:
            t = page["cleaned_text"] or ""
            if t.strip():
                for section in _split_by_paragraphs(t, max_size=800):
                    chunks.append({"page_number": page["page_number"], "text": section, "chunk_type": "daily_report_section"})

    else:
        for page in pages_data:
            t = page["cleaned_text"] or page["summary"] or ""
            if not t.strip():
                continue
            for chunk_text in _split_by_paragraphs(t, max_size=800, overlap=100):
                chunks.append({"page_number": page["page_number"], "text": chunk_text, "chunk_type": "general"})

    return chunks


def _split_by_paragraphs(t: str, max_size: int = 800, overlap: int = 100) -> list[str]:
    if len(t) <= max_size:
        return [t]
    chunks = []
    start = 0
    while start < len(t):
        end = start + max_size
        if end < len(t):
            bp = t.rfind("\n\n", start, end)
            if bp == -1 or bp <= start:
                bp = t.rfind(". ", start, end)
            if bp > start:
                end = bp + 1
        chunks.append(t[start:end].strip())
        start = end - overlap
    return [c for c in chunks if c.strip()]


def _embed_and_store(session, document_id, project_id, chunks, visibility_scope, trade_scope, doc_type):
    """Generate embeddings and store in pgvector."""
    texts = [c["text"] for c in chunks]

    try:
        embeddings = _get_embeddings(texts)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        # Store chunks without embeddings
        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            session.execute(
                text("""INSERT INTO document_chunks
                    (id, document_id, page_number, chunk_index, chunk_text, metadata_json,
                     visibility_scope, trade_scope, vector_id, created_at, updated_at)
                    VALUES (:id, :doc_id, :pn, :ci, :text, :meta, :vis, :trade, NULL, NOW(), NOW())"""),
                {
                    "id": chunk_id, "doc_id": document_id,
                    "pn": chunk["page_number"], "ci": i,
                    "text": chunk["text"],
                    "meta": json.dumps({"chunk_type": chunk["chunk_type"]}),
                    "vis": visibility_scope, "trade": trade_scope,
                },
            )
        session.commit()
        return

    # Store chunks with embeddings in pgvector
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = str(uuid.uuid4())
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        session.execute(
            text("""INSERT INTO document_chunks
                (id, document_id, page_number, chunk_index, chunk_text, metadata_json,
                 visibility_scope, trade_scope, vector_id, embedding, created_at, updated_at)
                VALUES (:id, :doc_id, :pn, :ci, :text, :meta, :vis, :trade, :vid, :emb::vector, NOW(), NOW())"""),
            {
                "id": chunk_id, "doc_id": document_id,
                "pn": chunk["page_number"], "ci": i,
                "text": chunk["text"],
                "meta": json.dumps({"chunk_type": chunk["chunk_type"]}),
                "vis": visibility_scope, "trade": trade_scope,
                "vid": chunk_id, "emb": embedding_str,
            },
        )

    session.commit()
    logger.info(f"Stored {len(chunks)} vectors for document {document_id}")


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    provider = os.environ.get("EMBEDDING_PROVIDER", settings.EMBEDDING_PROVIDER)

    if provider == "local":
        from fastembed import TextEmbedding
        model_name = os.environ.get("EMBEDDING_MODEL", settings.EMBEDDING_MODEL)
        model = TextEmbedding(model_name=model_name)
        return [emb.tolist() for emb in model.embed(texts)]
    else:
        import httpx
        base_url = settings.EMBEDDING_BASE_URL
        api_key = settings.EMBEDDING_API_KEY
        model = settings.EMBEDDING_MODEL
        all_embeddings = []
        batch_size = 32
        with httpx.Client(timeout=60) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                resp = client.post(
                    f"{base_url}/embeddings",
                    json={"model": model, "input": batch},
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                all_embeddings.extend([item["embedding"] for item in data["data"]])
        return all_embeddings
