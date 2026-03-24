from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.router import api_router

app = FastAPI(
    title="Construction RAG",
    description="Role-aware construction document chatbot API",
    version="1.0.0",
)

# Allow both configured origins and common deployment patterns
origins = list(settings.BACKEND_CORS_ORIGINS)
# Always allow localhost for dev
for o in ["http://localhost:3000", "http://127.0.0.1:3000"]:
    if o not in origins:
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
