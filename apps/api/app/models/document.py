from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, png, jpg
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # DocType
    visibility_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, default="project_full", index=True
    )
    trade_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    revision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="processing")  # DocStatus
    issue_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", lazy="noload", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", lazy="noload", cascade="all, delete-orphan")


class DocumentPage(TimestampMixin, Base):
    __tablename__ = "document_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_storage_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    document = relationship("Document", back_populates="pages")


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    visibility_scope: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    trade_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    vector_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    document = relationship("Document", back_populates="chunks")
