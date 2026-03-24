import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.deps import get_db, get_current_user, get_project_membership
from app.models.user import User
from app.models.membership import ProjectMembership
from app.models.document import Document, DocumentPage
from app.schemas.document import DocumentResponse, DocumentDetailResponse, PageResponse
from app.services.storage import upload_file, download_file, get_presigned_url
from app.services.audit_service import log_action
from app.rbac.filters import build_document_sql_filter
from shared.roles import ProjectRole, ROLE_PERMISSIONS

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
    membership: ProjectMembership = Depends(get_project_membership),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(build_document_sql_filter(membership, project_id))

    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if visibility_scope:
        query = query.where(Document.visibility_scope == visibility_scope)
    if trade_scope:
        query = query.where(Document.trade_scope == trade_scope)
    if status:
        query = query.where(Document.status == status)
    if search:
        query = query.where(Document.file_name.ilike(f"%{search}%"))

    query = query.order_by(Document.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()

    responses = []
    for d in docs:
        uploader = await db.get(User, d.uploaded_by_user_id)
        responses.append(DocumentResponse(
            id=d.id, project_id=d.project_id, file_name=d.file_name,
            file_type=d.file_type, doc_type=d.doc_type,
            visibility_scope=d.visibility_scope, trade_scope=d.trade_scope,
            revision=d.revision, status=d.status, issue_date=d.issue_date,
            page_count=d.page_count, processing_error=d.processing_error,
            uploaded_by_name=uploader.full_name if uploader else "",
            created_at=d.created_at,
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
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = ProjectRole(membership.role)
    if "document.upload" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to upload")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    file_data = await file.read()
    file_type = ext.lstrip(".")
    if file_type == "jpeg":
        file_type = "jpg"
    doc = Document(
        project_id=project_id,
        uploaded_by_user_id=user.id,
        file_name=file.filename or "unnamed",
        storage_key="",
        file_type=file_type,
        doc_type=doc_type,
        visibility_scope=visibility_scope,
        trade_scope=trade_scope,
        revision=revision,
        issue_date=issue_date,
        status="processing",
    )
    db.add(doc)
    await db.flush()

    storage_key = f"projects/{project_id}/documents/{doc.id}/original{ext}"
    upload_file(storage_key, file_data, content_type=file.content_type or "application/octet-stream")
    doc.storage_key = storage_key

    await log_action(db, "document.upload", user_id=user.id, project_id=project_id,
                     entity_type="document", entity_id=doc.id,
                     details={"file_name": doc.file_name, "doc_type": doc_type})
    await db.commit()
    await db.refresh(doc)

    # Dispatch background ingestion task (replaces Celery)
    from app.services.ingestion import ingest_document
    background_tasks.add_task(ingest_document, doc.id)

    return DocumentResponse(
        id=doc.id, project_id=doc.project_id, file_name=doc.file_name,
        file_type=doc.file_type, doc_type=doc.doc_type,
        visibility_scope=doc.visibility_scope, trade_scope=doc.trade_scope,
        revision=doc.revision, status=doc.status, issue_date=doc.issue_date,
        page_count=doc.page_count, uploaded_by_name=user.full_name,
        created_at=doc.created_at,
    )


@router.get("/projects/{project_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    project_id: str,
    document_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            build_document_sql_filter(membership, project_id),
            Document.id == document_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    pages = pages_result.scalars().all()

    await log_action(db, "document.view", user_id=user.id, project_id=project_id,
                     entity_type="document", entity_id=document_id)
    await db.commit()

    uploader = await db.get(User, doc.uploaded_by_user_id)
    return DocumentDetailResponse(
        id=doc.id, project_id=doc.project_id, file_name=doc.file_name,
        file_type=doc.file_type, doc_type=doc.doc_type,
        visibility_scope=doc.visibility_scope, trade_scope=doc.trade_scope,
        revision=doc.revision, status=doc.status, issue_date=doc.issue_date,
        page_count=doc.page_count, processing_error=doc.processing_error,
        uploaded_by_name=uploader.full_name if uploader else "",
        created_at=doc.created_at,
        metadata_json=doc.metadata_json,
        storage_key=doc.storage_key,
        pages=[PageResponse(
            id=p.id, page_number=p.page_number,
            page_summary=p.page_summary,
            image_storage_key=p.image_storage_key,
        ) for p in pages],
    )


@router.get("/projects/{project_id}/documents/{document_id}/download")
async def download_document(
    project_id: str,
    document_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            build_document_sql_filter(membership, project_id),
            Document.id == document_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    data = download_file(doc.storage_key)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )


@router.get("/projects/{project_id}/documents/{document_id}/pages/{page_number}/image")
async def get_page_image(
    project_id: str,
    document_id: str,
    page_number: int,
    membership: ProjectMembership = Depends(get_project_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            build_document_sql_filter(membership, project_id),
            Document.id == document_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    page_result = await db.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == document_id,
            DocumentPage.page_number == page_number,
        )
    )
    page = page_result.scalar_one_or_none()
    if not page or not page.image_storage_key:
        raise HTTPException(status_code=404, detail="Page image not found")

    data = download_file(page.image_storage_key)
    return StreamingResponse(io.BytesIO(data), media_type="image/png")
