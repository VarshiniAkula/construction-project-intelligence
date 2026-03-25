from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # Storage: "local" = filesystem | "supabase" = Supabase Storage
    STORAGE_BACKEND: str = "supabase"
    STORAGE_LOCAL_DIR: str = "./storage"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "documents"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- AI Provider Selection ---
    LLM_PROVIDER: str = "groq"

    # --- Groq (free-tier LLM) ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # --- Anthropic (Claude) ---
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_VISION_MODEL: str = "claude-sonnet-4-20250514"

    # --- OpenAI-compatible endpoints (fallback / local models) ---
    LLM_BASE_URL: str = "http://localhost:8081/v1"
    LLM_API_KEY: str = "not-needed"
    LLM_MODEL: str = "gpt-4o"

    VLM_BASE_URL: str = "http://localhost:8082/v1"
    VLM_API_KEY: str = "not-needed"
    VLM_MODEL: str = "gpt-4o"

    # --- Embeddings ---
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # --- Reranker ---
    RERANKER_PROVIDER: str = "local"
    RERANKER_BASE_URL: str = "http://localhost:8084/v1"
    RERANKER_API_KEY: str = "not-needed"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
