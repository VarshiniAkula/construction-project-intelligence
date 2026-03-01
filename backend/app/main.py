from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.session import engine
from app.db.base import Base
import app.db.models  # noqa: F401 (register models)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    # CORS for local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.on_event("startup")
    def on_startup():
        # MVP: auto-create tables. For production, use Alembic migrations.
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
