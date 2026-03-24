from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, get_project_membership
from app.models.user import User
from app.models.membership import ProjectMembership
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from shared.roles import ProjectRole, ROLE_PERMISSIONS

router = APIRouter()


@router.get("/projects/{project_id}/audit", response_model=list[AuditLogResponse])
async def list_audit_logs(
    project_id: str,
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = ProjectRole(membership.role)
    if "audit.view" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")

    query = (
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if action:
        query = query.where(AuditLog.action == action)

    result = await db.execute(query)
    logs = result.scalars().all()

    responses = []
    for log in logs:
        log_user = await db.get(User, log.user_id) if log.user_id else None
        responses.append(AuditLogResponse(
            id=log.id,
            project_id=log.project_id,
            user_id=log.user_id,
            user_email=log_user.email if log_user else "",
            user_name=log_user.full_name if log_user else "",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details_json=log.details_json,
            created_at=log.created_at,
        ))
    return responses
