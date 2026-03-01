from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # App
    APP_ENV: str = "dev"
    PROJECT_NAME: str = "Construction Project Intelligence"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="change-me", description="JWT signing key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    # Storage
    STORAGE_PATH: str = "./storage"
    FILE_ENCRYPTION_KEY: str | None = None

    # AI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Retrieval
    EMBEDDING_PROVIDER: str = "tfidf"  # tfidf | sentence_transformers
    SENTENCE_TRANSFORMERS_MODEL: str = "all-MiniLM-L6-v2"
    ASSISTANT_TOP_K: int = 5

    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
