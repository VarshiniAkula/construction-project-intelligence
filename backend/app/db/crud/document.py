from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models.document import Document


class DocumentCRUD:
    def get(self, db: Session, doc_id: str) -> Document | None:
        return db.get(Document, doc_id)

    def list_for_project(self, db: Session, *, project_id: str) -> list[Document]:
        stmt = select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def next_version(self, db: Session, *, project_id: str, original_filename: str) -> int:
        stmt = select(func.max(Document.version)).where(Document.project_id == project_id, Document.original_filename == original_filename)
        max_v = db.execute(stmt).scalar()
        return int(max_v or 0) + 1

    def create(
        self,
        db: Session,
        *,
        doc_id: str | None = None,
        project_id: str,
        original_filename: str,
        stored_filename: str,
        content_type: str | None,
        version: int,
        sha256: str,
        uploaded_by: str,
    ) -> Document:
        d = Document(
            id=doc_id,
            project_id=project_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            version=version,
            sha256=sha256,
            uploaded_by=uploaded_by,
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return d

    def mark_processed(self, db: Session, *, doc_id: str, extracted_text_chars: int) -> None:
        d = self.get(db, doc_id)
        if not d:
            return
        d.status = "processed"
        d.extracted_text_chars = extracted_text_chars
        d.error = None
        db.add(d)
        db.commit()

    def mark_error(self, db: Session, *, doc_id: str, error: str) -> None:
        d = self.get(db, doc_id)
        if not d:
            return
        d.status = "error"
        d.error = error
        db.add(d)
        db.commit()


document = DocumentCRUD()
