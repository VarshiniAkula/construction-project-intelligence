import uuid
from fastapi import APIRouter, Depends, HTTPException
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, get_project_membership
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageRequest, ChatMessageResponse, ChatAnswerResponse,
)
from app.services.chat_service import process_chat_message

router = APIRouter()


@router.get("/projects/{project_id}/chat/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    project_id: str,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    result = await sb.table("chat_sessions").select("*").eq("project_id", project_id).eq("user_id", user.id).order("updated_at", desc=True).execute()
    sessions = result.data

    responses = []
    for s in sessions:
        last_msg_result = await sb.table("chat_messages").select("content").eq("session_id", s["id"]).order("created_at", desc=True).limit(1).execute()
        last_msg = last_msg_result.data[0] if last_msg_result.data else None
        responses.append(ChatSessionResponse(
            id=s["id"], project_id=s["project_id"], title=s["title"],
            created_at=s["created_at"],
            last_message=last_msg["content"][:100] if last_msg else None,
        ))
    return responses


@router.post("/projects/{project_id}/chat/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    project_id: str,
    body: ChatSessionCreate,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    session_data = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "user_id": user.id,
        "title": body.title,
    }
    result = await sb.table("chat_sessions").insert(session_data).execute()
    session = result.data[0]
    return ChatSessionResponse(
        id=session["id"], project_id=session["project_id"],
        title=session["title"], created_at=session["created_at"],
    )


@router.get("/projects/{project_id}/chat/sessions/{session_id}", response_model=list[ChatMessageResponse])
async def get_session_messages(
    project_id: str,
    session_id: str,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    session_result = await sb.table("chat_sessions").select("*").eq("id", session_id).maybe_single().execute()
    session = session_result.data
    if not session or session["project_id"] != project_id or session["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await sb.table("chat_messages").select("*").eq("session_id", session_id).order("created_at").execute()
    messages = result.data

    return [
        ChatMessageResponse(
            id=m["id"], session_id=m["session_id"], role=m["role"],
            content=m["content"],
            citations=m.get("citations_json") or [],
            model_metadata=m.get("model_metadata_json"),
            created_at=m["created_at"],
        )
        for m in messages
    ]


@router.post("/projects/{project_id}/chat/sessions/{session_id}/messages", response_model=ChatAnswerResponse)
async def send_message(
    project_id: str,
    session_id: str,
    body: ChatMessageRequest,
    membership=Depends(get_project_membership),
    user=Depends(get_current_user),
    sb: AsyncClient = Depends(get_sb),
):
    session_result = await sb.table("chat_sessions").select("*").eq("id", session_id).maybe_single().execute()
    session = session_result.data
    if not session or session["project_id"] != project_id or session["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    return await process_chat_message(
        sb=sb,
        user_id=user.id,
        project_id=project_id,
        session_id=session_id,
        membership=membership,
        content=body.content,
    )
