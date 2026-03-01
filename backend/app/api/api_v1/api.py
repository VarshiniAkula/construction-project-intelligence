from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, projects, documents, assistant, rfi, analytics, schedules, budgets

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/projects", tags=["documents"])
api_router.include_router(assistant.router, prefix="/projects", tags=["assistant"])
api_router.include_router(rfi.router, prefix="/projects", tags=["rfis"])
api_router.include_router(analytics.router, prefix="/projects", tags=["analytics"])
api_router.include_router(schedules.router, prefix="/projects", tags=["schedule"])
api_router.include_router(budgets.router, prefix="/projects", tags=["budget"])
