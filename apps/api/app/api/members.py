import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, get_project_membership
from app.schemas.member import MemberAdd, MemberUpdate, MemberResponse
from app.services.audit_service import log_action
from app.shared_roles import ProjectRole, ROLE_PERMISSIONS

router = APIRouter()


def _check_manage_permission(membership):
    role = ProjectRole(membership.role)
    if "member.manage" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to manage members")


@router.get("/projects/{project_id}/members", response_model=list[MemberResponse])
async def list_members(
    project_id: str,
    membership=Depends(get_project_membership),
    sb: AsyncClient = Depends(get_sb),
):
    result = await sb.table("project_memberships").select("*").eq("project_id", project_id).execute()
    members = result.data
    responses = []
    for m in members:
        u_result = await sb.table("users").select("email,full_name,company_name").eq("id", m["user_id"]).maybe_single().execute()
        u = u_result.data
        responses.append(MemberResponse(
            id=m["id"], user_id=m["user_id"], project_id=m["project_id"],
            role=m["role"], assigned_trade=m.get("assigned_trade"),
            user_email=u["email"] if u else "",
            user_full_name=u["full_name"] if u else "",
            user_company=u.get("company_name") if u else None,
            created_at=m["created_at"],
        ))
    return responses


@router.post("/projects/{project_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    project_id: str,
    body: MemberAdd,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    _check_manage_permission(membership)

    u_result = await sb.table("users").select("*").eq("email", body.email).maybe_single().execute()
    target_user = u_result.data
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await sb.table("project_memberships").select("id").eq("user_id", target_user["id"]).eq("project_id", project_id).maybe_single().execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Already a member")

    mem_data = {
        "id": str(uuid.uuid4()),
        "user_id": target_user["id"],
        "project_id": project_id,
        "role": body.role,
        "assigned_trade": body.assigned_trade,
    }
    result = await sb.table("project_memberships").insert(mem_data).execute()
    new_mem = result.data[0]

    await log_action(sb, "member.add", user_id=user.id, project_id=project_id,
                     entity_type="membership", details={"target_email": body.email, "role": body.role})

    return MemberResponse(
        id=new_mem["id"], user_id=target_user["id"], project_id=project_id,
        role=new_mem["role"], assigned_trade=new_mem.get("assigned_trade"),
        user_email=target_user["email"], user_full_name=target_user["full_name"],
        user_company=target_user.get("company_name"), created_at=new_mem["created_at"],
    )


@router.patch("/projects/{project_id}/members/{membership_id}", response_model=MemberResponse)
async def update_member(
    project_id: str,
    membership_id: str,
    body: MemberUpdate,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    _check_manage_permission(membership)

    target_result = await sb.table("project_memberships").select("*").eq("id", membership_id).maybe_single().execute()
    target = target_result.data
    if not target or target["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="Membership not found")

    updates = {}
    if body.role is not None:
        updates["role"] = body.role
    if body.assigned_trade is not None:
        updates["assigned_trade"] = body.assigned_trade

    if updates:
        await sb.table("project_memberships").update(updates).eq("id", membership_id).execute()
        # Re-fetch
        target_result = await sb.table("project_memberships").select("*").eq("id", membership_id).maybe_single().execute()
        target = target_result.data

    await log_action(sb, "member.update", user_id=user.id, project_id=project_id,
                     entity_type="membership", entity_id=membership_id,
                     details={"changes": body.model_dump(exclude_none=True)})

    u_result = await sb.table("users").select("email,full_name,company_name").eq("id", target["user_id"]).maybe_single().execute()
    u = u_result.data
    return MemberResponse(
        id=target["id"], user_id=target["user_id"], project_id=target["project_id"],
        role=target["role"], assigned_trade=target.get("assigned_trade"),
        user_email=u["email"] if u else "",
        user_full_name=u["full_name"] if u else "",
        user_company=u.get("company_name") if u else None,
        created_at=target["created_at"],
    )
