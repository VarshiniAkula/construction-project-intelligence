from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, get_project_membership
from app.models.user import User
from app.models.membership import ProjectMembership
from app.schemas.member import MemberAdd, MemberUpdate, MemberResponse
from app.services.audit_service import log_action
from shared.roles import ProjectRole, ROLE_PERMISSIONS

router = APIRouter()


def _check_manage_permission(membership: ProjectMembership):
    role = ProjectRole(membership.role)
    if "member.manage" not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(status_code=403, detail="Not authorized to manage members")


@router.get("/projects/{project_id}/members", response_model=list[MemberResponse])
async def list_members(
    project_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.project_id == project_id)
    )
    members = result.scalars().all()
    responses = []
    for m in members:
        user = await db.get(User, m.user_id)
        responses.append(MemberResponse(
            id=m.id, user_id=m.user_id, project_id=m.project_id,
            role=m.role, assigned_trade=m.assigned_trade,
            user_email=user.email if user else "",
            user_full_name=user.full_name if user else "",
            user_company=user.company_name if user else None,
            created_at=m.created_at,
        ))
    return responses


@router.post("/projects/{project_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    project_id: str,
    body: MemberAdd,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_manage_permission(membership)

    result = await db.execute(select(User).where(User.email == body.email))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id == target_user.id,
            ProjectMembership.project_id == project_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    new_membership = ProjectMembership(
        user_id=target_user.id, project_id=project_id,
        role=body.role, assigned_trade=body.assigned_trade,
    )
    db.add(new_membership)
    await log_action(db, "member.add", user_id=user.id, project_id=project_id,
                     entity_type="membership", details={"target_email": body.email, "role": body.role})
    await db.commit()
    await db.refresh(new_membership)

    return MemberResponse(
        id=new_membership.id, user_id=target_user.id, project_id=project_id,
        role=new_membership.role, assigned_trade=new_membership.assigned_trade,
        user_email=target_user.email, user_full_name=target_user.full_name,
        user_company=target_user.company_name, created_at=new_membership.created_at,
    )


@router.patch("/projects/{project_id}/members/{membership_id}", response_model=MemberResponse)
async def update_member(
    project_id: str,
    membership_id: str,
    body: MemberUpdate,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_manage_permission(membership)

    target = await db.get(ProjectMembership, membership_id)
    if not target or target.project_id != project_id:
        raise HTTPException(status_code=404, detail="Membership not found")

    if body.role is not None:
        target.role = body.role
    if body.assigned_trade is not None:
        target.assigned_trade = body.assigned_trade

    await log_action(db, "member.update", user_id=user.id, project_id=project_id,
                     entity_type="membership", entity_id=membership_id,
                     details={"changes": body.model_dump(exclude_none=True)})
    await db.commit()
    await db.refresh(target)

    target_user = await db.get(User, target.user_id)
    return MemberResponse(
        id=target.id, user_id=target.user_id, project_id=target.project_id,
        role=target.role, assigned_trade=target.assigned_trade,
        user_email=target_user.email if target_user else "",
        user_full_name=target_user.full_name if target_user else "",
        user_company=target_user.company_name if target_user else None,
        created_at=target.created_at,
    )
