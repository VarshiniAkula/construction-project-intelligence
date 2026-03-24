"""Audit logging service."""
import uuid
from supabase._async.client import AsyncClient


async def log_action(
    sb: AsyncClient,
    action: str,
    user_id: str | None = None,
    project_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
) -> None:
    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "project_id": project_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details_json": details,
    }
    await sb.table("audit_logs").insert(entry).execute()
