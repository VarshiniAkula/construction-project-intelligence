import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, _single
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user=Depends(get_current_user), sb: AsyncClient = Depends(get_sb)):
    if user.is_superadmin:
        result = await sb.table("projects").select("*").order("created_at", desc=True).execute()
        projects = result.data
    else:
        # Get project IDs from memberships
        mem_result = await sb.table("project_memberships").select("project_id").eq("user_id", user.id).execute()
        project_ids = [m["project_id"] for m in mem_result.data]
        if not project_ids:
            return []
        result = await sb.table("projects").select("*").in_("id", project_ids).order("created_at", desc=True).execute()
        projects = result.data

    responses = []
    for p in projects:
        mem_count = (await sb.table("project_memberships").select("id", count="exact").eq("project_id", p["id"]).execute()).count or 0
        doc_count = (await sb.table("documents").select("id", count="exact").eq("project_id", p["id"]).execute()).count or 0
        my_mem = _single(await sb.table("project_memberships").select("role").eq("project_id", p["id"]).eq("user_id", user.id).maybe_single().execute())
        my_role = my_mem["role"] if my_mem else ("admin" if user.is_superadmin else None)
        responses.append(ProjectResponse(
            id=p["id"], name=p["name"], code=p["code"],
            location=p.get("location"), description=p.get("description"),
            created_at=p["created_at"],
            member_count=mem_count, document_count=doc_count, my_role=my_role,
        ))
    return responses


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, user=Depends(get_current_user), sb: AsyncClient = Depends(get_sb)):
    existing = _single(await sb.table("projects").select("id").eq("code", body.code).maybe_single().execute())
    if existing:
        raise HTTPException(status_code=400, detail="Project code already exists")

    project_id = str(uuid.uuid4())
    proj_data = {"id": project_id, "name": body.name, "code": body.code, "location": body.location, "description": body.description}
    result = await sb.table("projects").insert(proj_data).execute()
    project = result.data[0]

    mem_data = {"id": str(uuid.uuid4()), "user_id": user.id, "project_id": project_id, "role": "admin"}
    await sb.table("project_memberships").insert(mem_data).execute()

    await log_action(sb, "project.create", user_id=user.id, project_id=project_id, entity_type="project", entity_id=project_id)

    return ProjectResponse(
        id=project["id"], name=project["name"], code=project["code"],
        location=project.get("location"), description=project.get("description"),
        created_at=project["created_at"], member_count=1, document_count=0, my_role="admin",
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, user=Depends(get_current_user), sb: AsyncClient = Depends(get_sb)):
    project = _single(await sb.table("projects").select("*").eq("id", project_id).maybe_single().execute())
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not user.is_superadmin:
        mem = _single(await sb.table("project_memberships").select("id").eq("project_id", project_id).eq("user_id", user.id).maybe_single().execute())
        if not mem:
            raise HTTPException(status_code=403, detail="Not a member")

    mem_count = (await sb.table("project_memberships").select("id", count="exact").eq("project_id", project_id).execute()).count or 0
    doc_count = (await sb.table("documents").select("id", count="exact").eq("project_id", project_id).execute()).count or 0
    my_mem = _single(await sb.table("project_memberships").select("role").eq("project_id", project_id).eq("user_id", user.id).maybe_single().execute())
    my_role = my_mem["role"] if my_mem else ("admin" if user.is_superadmin else None)

    return ProjectResponse(
        id=project["id"], name=project["name"], code=project["code"],
        location=project.get("location"), description=project.get("description"),
        created_at=project["created_at"],
        member_count=mem_count, document_count=doc_count, my_role=my_role,
    )
