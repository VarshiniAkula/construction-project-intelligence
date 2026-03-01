from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import crud
from app.db.models.document import Document
from app.services.storage import read_document_bytes
from app.services.vectorstore import vectorstore
from app.utils.text_extract import extract_text_from_bytes
from app.utils.chunking import chunk_text


def ingest_document(db: Session, document: Document) -> None:
    '''
    Background ingestion:
    - reads the uploaded file
    - extracts text (best effort)
    - chunks it
    - updates the project-level vector index
    '''
    try:
        data = read_document_bytes(document.project_id, document.id, document.version, document.stored_filename)
        text = extract_text_from_bytes(document.original_filename, data, document.content_type)
        if not text:
            crud.document.mark_error(db, doc_id=document.id, error="No extractable text found. If this is a scanned PDF, OCR is not enabled in this MVP.")
            return

        chunks = chunk_text(text, max_chars=1200, overlap=150)
        if not chunks:
            crud.document.mark_error(db, doc_id=document.id, error="Text extraction succeeded but produced no chunks.")
            return

        vectorstore.add_chunks(
            document.project_id,
            document_id=document.id,
            filename=document.original_filename,
            version=document.version,
            chunks=[c.text for c in chunks],
        )
        crud.document.mark_processed(db, doc_id=document.id, extracted_text_chars=len(text))
    except Exception as e:
        crud.document.mark_error(db, doc_id=document.id, error=str(e))
