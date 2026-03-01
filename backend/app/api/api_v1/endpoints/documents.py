from __future__ import annotations

import mimetypes
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member, require_project_role
from app.db import crud
from app.db.models.membership import ProjectRole
from app.db.session import SessionLocal
from app.services.storage import save_document_bytes, read_document_bytes, delete_project_index
from app.services.ingestion import ingest_document
from app.services.vectorstore import vectorstore
from app import schemas

router = APIRouter()


def _background_ingest(doc_id: str) -> None:
    db = SessionLocal()
    try:
        doc = crud.document.get(db, doc_id)
        if not doc:
            return
        ingest_document(db, doc)
    finally:
        db.close()


@router.get("/{project_id}/documents", response_model=list[schemas.DocumentOut])
def list_documents(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    return crud.document.list_for_project(db, project_id=project_id)


@router.post("/{project_id}/documents", response_model=schemas.DocumentOut)
async def upload_document(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    membership=Depends(require_project_member),
    request: Request = None,
):
    original = file.filename or "upload.bin"
    version = crud.document.next_version(db, project_id=project_id, original_filename=original)
    doc_id = str(uuid.uuid4())

    ext = ""
    if "." in original:
        ext = "." + original.split(".")[-1]
    stored_filename = f"{doc_id}{ext}"

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256_hex, storage_mode, path = save_document_bytes(project_id, doc_id, version, stored_filename, data)

    doc = crud.document.create(
        db,
        doc_id=doc_id,
        project_id=project_id,
        original_filename=original,
        stored_filename=stored_filename,
        content_type=file.content_type,
        version=version,
        sha256=sha256_hex,
        uploaded_by=user.id,
    )

    crud.audit.log(
        db,
        user_id=user.id,
        project_id=project_id,
        action="document.upload",
        details={"document_id": doc.id, "filename": doc.original_filename, "version": doc.version, "storage_mode": storage_mode},
        ip_address=getattr(request.client, "host", None) if request else None,
    )

    background_tasks.add_task(_background_ingest, doc.id)
    return doc


@router.get("/{project_id}/documents/{doc_id}/download")
def download_document(project_id: str, doc_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    doc = crud.document.get(db, doc_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    data = read_document_bytes(project_id, doc.id, doc.version, doc.stored_filename)
    ctype = doc.content_type or mimetypes.guess_type(doc.original_filename)[0] or "application/octet-stream"

    def iter_bytes():
        yield data

    headers = {"Content-Disposition": f'attachment; filename="{doc.original_filename}"'}
    return StreamingResponse(iter_bytes(), media_type=ctype, headers=headers)


@router.post("/{project_id}/documents/rebuild_index")
def rebuild_index(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_role([ProjectRole.PROJECT_MANAGER]))):
    # just rebuild TF-IDF from existing chunks.jsonl
    vectorstore.rebuild(project_id)
    return {"ok": True}


@router.post("/{project_id}/documents/reindex_all")
def reindex_all(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_role([ProjectRole.PROJECT_MANAGER]))):
    # Clear index and re-ingest every document in the project.
    delete_project_index(project_id)
    docs = crud.document.list_for_project(db, project_id=project_id)
    for d in docs:
        ingest_document(db, d)
    return {"ok": True, "documents": len(docs)}
