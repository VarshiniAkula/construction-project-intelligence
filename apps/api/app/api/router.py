from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.members import router as members_router
from app.api.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(members_router, tags=["members"])
api_router.include_router(audit_router, tags=["audit"])
