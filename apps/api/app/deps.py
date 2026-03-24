"""FastAPI dependencies using Supabase PostgREST."""
from types import SimpleNamespace
from fastapi import Depends, HTTPException, Request, status
from supabase._async.client import AsyncClient

from app.supabase_client import get_supabase
from app.security.jwt import decode_token


def _row_to_ns(row: dict) -> SimpleNamespace:
    """Convert a dict row to SimpleNamespace for attribute access."""
    return SimpleNamespace(**row)


async def get_sb() -> AsyncClient:
    return await get_supabase()


async def get_current_user(
    request: Request,
    sb: AsyncClient = Depends(get_sb),
) -> SimpleNamespace:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    result = await sb.table("users").select("*").eq("id", user_id).maybe_single().execute()
    user = result.data
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _row_to_ns(user)


async def get_project_membership(
    project_id: str,
    user: SimpleNamespace = Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
) -> SimpleNamespace:
    if user.is_superadmin:
        return SimpleNamespace(
            id="superadmin",
            user_id=user.id,
            project_id=project_id,
            role="admin",
            assigned_trade=None,
        )

    result = await sb.table("project_memberships").select("*").eq("user_id", user.id).eq("project_id", project_id).maybe_single().execute()
    membership = result.data
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")
    return _row_to_ns(membership)
