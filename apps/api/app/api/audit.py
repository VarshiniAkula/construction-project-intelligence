from fastapi import APIRouter, Depends, HTTPException, Query
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, get_project_membership, _single
from app.schemas.audit import AuditLogResponse
from app.shared_roles import ProjectRole, ROLE_PERMISSIONS

router = APIRouter()


@router.get("/projects/{project_id}/audit", response_model=list[AuditLogResponse])
async def list_audit_logs(
    project_id: str,
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    role = ProjectRole(membership.role)
    if "audit.view" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")

    query = sb.table("audit_logs").select("*").eq("project_id", project_id).order("created_at", desc=True).range(offset, offset + limit - 1)

    if action:
        query = query.eq("action", action)

    result = await query.execute()
    logs = result.data

    responses = []
    for log in logs:
        log_user = None
        if log.get("user_id"):
            log_user = _single(await sb.table("users").select("email,full_name").eq("id", log["user_id"]).maybe_single().execute())
        responses.append(AuditLogResponse(
            id=log["id"],
            project_id=log.get("project_id"),
            user_id=log.get("user_id"),
            user_email=log_user["email"] if log_user else "",
            user_name=log_user["full_name"] if log_user else "",
            action=log["action"],
            entity_type=log.get("entity_type"),
            entity_id=log.get("entity_id"),
            details_json=log.get("details_json"),
            created_at=log["created_at"],
        ))
    return responses
