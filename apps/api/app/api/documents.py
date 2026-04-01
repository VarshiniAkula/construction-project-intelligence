import os
import io
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, get_project_membership, _single
from app.schemas.document import DocumentResponse, DocumentDetailResponse, PageResponse
from app.services.storage import upload_file, download_file
from app.services.audit_service import log_action
from app.rbac.filters import get_allowed_scopes
from app.shared_roles import ProjectRole, ROLE_PERMISSIONS

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".csv"}


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: str,
    doc_type: str | None = Query(None),
    visibility_scope: str | None = Query(None),
    trade_scope: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    membership=Depends(get_project_membership),
    sb: AsyncClient = Depends(get_sb),
):
    allowed_scopes = get_allowed_scopes(membership)
    query = sb.table("documents").select("*").eq("project_id", project_id).in_("visibility_scope", allowed_scopes)

    # Subcontractor trade filtering
    if membership.role == "subcontractor" and membership.assigned_trade:
        # We can't do complex OR filters easily in PostgREST, so we'll filter in Python
        pass

    if doc_type:
        query = query.eq("doc_type", doc_type)
    if visibility_scope:
        query = query.eq("visibility_scope", visibility_scope)
    if trade_scope:
        query = query.eq("trade_scope", trade_scope)
    if status:
        query = query.eq("status", status)
    if search:
        query = query.ilike("file_name", f"%{search}%")

    query = query.order("created_at", desc=True)
    result = await query.execute()
    docs = result.data

    # Apply subcontractor trade filtering in Python
    if membership.role == "subcontractor" and membership.assigned_trade:
        docs = [
            d for d in docs
            if d["visibility_scope"] != "trade_scoped"
            or d.get("trade_scope") == membership.assigned_trade
            or d.get("trade_scope") is None
        ]

    responses = []
    for d in docs:
        uploader_name = ""
        if d.get("uploaded_by"):
            u = _single(await sb.table("users").select("full_name").eq("id", d["uploaded_by"]).maybe_single().execute())
            if u:
                uploader_name = u["full_name"]
        responses.append(DocumentResponse(
            id=d["id"], project_id=d["project_id"], file_name=d["file_name"],
            file_type=d["file_type"], doc_type=d["doc_type"],
            visibility_scope=d["visibility_scope"], trade_scope=d.get("trade_scope"),
            revision=d.get("revision"), status=d["status"], issue_date=d.get("issue_date"),
            page_count=d.get("page_count"), processing_error=d.get("processing_error"),
            uploaded_by_name=uploader_name, created_at=d["created_at"],
        ))
    return responses


@router.post("/projects/{project_id}/documents/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form("general"),
    visibility_scope: str = Form("project_full"),
    trade_scope: str | None = Form(None),
    revision: str | None = Form(None),
    issue_date: str | None = Form(None),
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    import logging
    logger = logging.getLogger(__name__)

    role = ProjectRole(membership.role)
    if "document.upload" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to upload")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    try:
        file_data = await file.read()
        file_type = ext.lstrip(".")
        if file_type == "jpeg":
            file_type = "jpg"

        doc_id = str(uuid.uuid4())
        storage_key = f"projects/{project_id}/documents/{doc_id}/original{ext}"
        upload_file(storage_key, file_data, content_type=file.content_type or "application/octet-stream")

        doc_data = {
            "id": doc_id,
            "project_id": project_id,
            "uploaded_by": user.id,
            "file_name": file.filename or "unnamed",
            "storage_key": storage_key,
            "file_type": file_type,
            "doc_type": doc_type,
            "visibility_scope": visibility_scope,
            "trade_scope": trade_scope,
            "revision": revision,
            "issue_date": issue_date,
            "status": "processing",
        }
        result = await sb.table("documents").insert(doc_data).execute()
        doc = result.data[0]

        await log_action(sb, "document.upload", user_id=user.id, project_id=project_id,
                         entity_type="document", entity_id=doc_id,
                         details={"file_name": doc["file_name"], "doc_type": doc_type})

        # Dispatch ingestion: inline on Vercel (serverless), background otherwise
        try:
            if os.environ.get("VERCEL"):
                from app.services.ingestion import ingest_document_lightweight
                ingest_document_lightweight(doc_id)
                # Refresh doc status after inline ingestion
                refreshed = await sb.table("documents").select("*").eq("id", doc_id).maybe_single().execute()
                if refreshed and refreshed.data:
                    doc = refreshed.data
            else:
                from app.services.ingestion import ingest_document
                background_tasks.add_task(ingest_document, doc_id)
        except Exception as ing_err:
            logger.warning(f"Could not schedule ingestion: {ing_err}")

        return DocumentResponse(
            id=doc["id"], project_id=doc["project_id"], file_name=doc["file_name"],
            file_type=doc["file_type"], doc_type=doc["doc_type"],
            visibility_scope=doc["visibility_scope"], trade_scope=doc.get("trade_scope"),
            revision=doc.get("revision"), status=doc["status"], issue_date=doc.get("issue_date"),
            page_count=doc.get("page_count"), uploaded_by_name=user.full_name,
            created_at=doc["created_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/projects/{project_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    project_id: str,
    document_id: str,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    allowed_scopes = get_allowed_scopes(membership)
    doc = _single(await sb.table("documents").select("*").eq("id", document_id).eq("project_id", project_id).in_("visibility_scope", allowed_scopes).maybe_single().execute())
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Subcontractor trade check
    if membership.role == "subcontractor" and membership.assigned_trade:
        if doc["visibility_scope"] == "trade_scoped" and doc.get("trade_scope") != membership.assigned_trade and doc.get("trade_scope") is not None:
            raise HTTPException(status_code=404, detail="Document not found")

    pages_result = await sb.table("document_pages").select("*").eq("document_id", document_id).order("page_number").execute()
    pages = pages_result.data

    await log_action(sb, "document.view", user_id=user.id, project_id=project_id,
                     entity_type="document", entity_id=document_id)

    uploader_name = ""
    if doc.get("uploaded_by"):
        u = _single(await sb.table("users").select("full_name").eq("id", doc["uploaded_by"]).maybe_single().execute())
        if u:
            uploader_name = u["full_name"]

    return DocumentDetailResponse(
        id=doc["id"], project_id=doc["project_id"], file_name=doc["file_name"],
        file_type=doc["file_type"], doc_type=doc["doc_type"],
        visibility_scope=doc["visibility_scope"], trade_scope=doc.get("trade_scope"),
        revision=doc.get("revision"), status=doc["status"], issue_date=doc.get("issue_date"),
        page_count=doc.get("page_count"), processing_error=doc.get("processing_error"),
        uploaded_by_name=uploader_name, created_at=doc["created_at"],
        metadata_json=doc.get("metadata_json"),
        storage_key=doc.get("storage_key", ""),
        pages=[PageResponse(
            id=p["id"], page_number=p["page_number"],
            page_summary=p.get("page_summary"),
            image_storage_key=p.get("image_storage_key"),
        ) for p in pages],
    )


@router.get("/projects/{project_id}/documents/{document_id}/download")
async def download_document(
    project_id: str,
    document_id: str,
    membership=Depends(get_project_membership),
    sb: AsyncClient = Depends(get_sb),
):
    allowed_scopes = get_allowed_scopes(membership)
    doc = _single(await sb.table("documents").select("*").eq("id", document_id).eq("project_id", project_id).in_("visibility_scope", allowed_scopes).maybe_single().execute())
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    data = download_file(doc["storage_key"])
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc["file_name"]}"'},
    )


@router.get("/projects/{project_id}/documents/{document_id}/pages/{page_number}/image")
async def get_page_image(
    project_id: str,
    document_id: str,
    page_number: int,
    membership=Depends(get_project_membership),
    sb: AsyncClient = Depends(get_sb),
):
    allowed_scopes = get_allowed_scopes(membership)
    doc_check = _single(await sb.table("documents").select("id").eq("id", document_id).eq("project_id", project_id).in_("visibility_scope", allowed_scopes).maybe_single().execute())
    if not doc_check:
        raise HTTPException(status_code=404, detail="Document not found")

    page = _single(await sb.table("document_pages").select("*").eq("document_id", document_id).eq("page_number", page_number).maybe_single().execute())
    if not page or not page.get("image_storage_key"):
        raise HTTPException(status_code=404, detail="Page image not found")

    data = download_file(page["image_storage_key"])
    return StreamingResponse(io.BytesIO(data), media_type="image/png")


@router.post("/projects/{project_id}/documents/{document_id}/reprocess")
async def reprocess_document(
    project_id: str,
    document_id: str,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    """Synchronous reprocess: reads existing pages, creates chunks, marks document ready.

    Useful for documents stuck at 'chunking' status due to serverless timeouts.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Verify document exists and belongs to project
    doc = _single(await sb.table("documents").select("*").eq("id", document_id).eq("project_id", project_id).maybe_single().execute())
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Read existing pages (only fields needed for chunking)
    pages_result = await sb.table("document_pages").select("page_number,raw_text,cleaned_text,page_summary").eq("document_id", document_id).order("page_number").execute()
    pages = pages_result.data
    if not pages:
        raise HTTPException(status_code=400, detail="No pages found for document. Re-upload may be required.")

    pages_data = [
        {
            "page_number": p["page_number"],
            "raw_text": p.get("raw_text") or "",
            "cleaned_text": p.get("cleaned_text") or "",
            "summary": p.get("page_summary") or "",
        }
        for p in pages
    ]

    # Delete existing chunks and create new ones in parallel
    delete_task = sb.table("document_chunks").delete().eq("document_id", document_id).execute()

    from app.services.ingestion import _chunk_pages
    chunks = _chunk_pages(pages_data, doc.get("doc_type", "general"))
    logger.info(f"Reprocess: created {len(chunks)} chunks for document {document_id}")

    await delete_task  # ensure delete completes before insert

    visibility_scope = doc.get("visibility_scope", "project_full")
    trade_scope = doc.get("trade_scope") or ""
    doc_type = doc.get("doc_type", "general")

    # Build all chunk rows, then single batch insert (faster than multiple batches)
    batch = []
    for i, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        batch.append({
            "id": chunk_id,
            "document_id": document_id,
            "page_number": chunk["page_number"],
            "chunk_index": i,
            "chunk_text": chunk["text"],
            "doc_type": doc_type,
            "metadata_json": {"chunk_type": chunk["chunk_type"]},
            "visibility_scope": visibility_scope,
            "trade_scope": trade_scope,
            "vector_id": chunk_id,
        })

    # Insert all at once if under 100, else batch by 100 (larger batches = fewer round trips)
    for b_start in range(0, len(batch), 100):
        await sb.table("document_chunks").insert(batch[b_start:b_start + 100]).execute()

    await sb.table("documents").update({"status": "ready", "processing_error": None}).eq("id", document_id).execute()

    return {"status": "ready", "chunks_created": len(chunks)}
