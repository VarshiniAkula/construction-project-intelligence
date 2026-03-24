from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user, get_project_membership
from app.models.user import User
from app.models.membership import ProjectMembership
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageRequest, ChatMessageResponse, ChatAnswerResponse,
)
from app.services.chat_service import process_chat_message

router = APIRouter()


@router.get("/projects/{project_id}/chat/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    project_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.project_id == project_id, ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    responses = []
    for s in sessions:
        last_msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        responses.append(ChatSessionResponse(
            id=s.id, project_id=s.project_id, title=s.title,
            created_at=s.created_at,
            last_message=last_msg.content[:100] if last_msg else None,
        ))
    return responses


@router.post("/projects/{project_id}/chat/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    project_id: str,
    body: ChatSessionCreate,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(
        project_id=project_id,
        user_id=user.id,
        title=body.title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=session.id, project_id=session.project_id,
        title=session.title, created_at=session.created_at,
    )


@router.get("/projects/{project_id}/chat/sessions/{session_id}", response_model=list[ChatMessageResponse])
async def get_session_messages(
    project_id: str,
    session_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.project_id != project_id or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        ChatMessageResponse(
            id=m.id, session_id=m.session_id, role=m.role,
            content=m.content,
            citations=m.citations_json or [],
            model_metadata=m.model_metadata_json,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/projects/{project_id}/chat/sessions/{session_id}/messages", response_model=ChatAnswerResponse)
async def send_message(
    project_id: str,
    session_id: str,
    body: ChatMessageRequest,
    membership: ProjectMembership = Depends(get_project_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(ChatSession, session_id)
    if not session or session.project_id != project_id or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    return await process_chat_message(
        db=db,
        user_id=user.id,
        project_id=project_id,
        session_id=session_id,
        membership=membership,
        content=body.content,
    )
