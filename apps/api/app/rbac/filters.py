"""Build SQL filters based on user role and project membership."""
from sqlalchemy import and_, or_

from app.models.document import Document, DocumentChunk
from app.models.membership import ProjectMembership
from shared.roles import ProjectRole, VisibilityScope, ROLE_VISIBILITY_MAP


def get_allowed_scopes(membership: ProjectMembership) -> list[str]:
    role = ProjectRole(membership.role)
    return [s.value for s in ROLE_VISIBILITY_MAP.get(role, set())]


def build_document_sql_filter(membership: ProjectMembership, project_id: str):
    """Return SQLAlchemy WHERE clause for document access."""
    allowed_scopes = get_allowed_scopes(membership)
    conditions = [
        Document.project_id == project_id,
        Document.visibility_scope.in_(allowed_scopes),
    ]

    role = ProjectRole(membership.role)
    if role == ProjectRole.SUBCONTRACTOR:
        trade = membership.assigned_trade
        conditions.append(
            or_(
                Document.visibility_scope != VisibilityScope.TRADE_SCOPED.value,
                Document.trade_scope == trade,
                Document.trade_scope.is_(None),
            )
        )

    return and_(*conditions)


def build_chunk_sql_filter(membership: ProjectMembership, project_id: str):
    """Return SQLAlchemy WHERE clause for chunk access."""
    allowed_scopes = get_allowed_scopes(membership)
    from sqlalchemy import select
    doc_subq = select(Document.id).where(Document.project_id == project_id).subquery()

    conditions = [
        DocumentChunk.document_id.in_(select(doc_subq.c.id)),
        DocumentChunk.visibility_scope.in_(allowed_scopes),
    ]

    role = ProjectRole(membership.role)
    if role == ProjectRole.SUBCONTRACTOR:
        trade = membership.assigned_trade
        conditions.append(
            or_(
                DocumentChunk.visibility_scope != VisibilityScope.TRADE_SCOPED.value,
                DocumentChunk.trade_scope == trade,
                DocumentChunk.trade_scope.is_(None),
            )
        )

    return and_(*conditions)
