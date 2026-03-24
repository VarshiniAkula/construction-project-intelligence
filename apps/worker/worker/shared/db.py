"""Synchronous database session for the Celery worker."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Worker uses sync engine
db_url = os.environ.get("DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL", "postgresql+psycopg://builddocs:builddocs@localhost:5432/builddocs")
if db_url.startswith("postgresql+asyncpg"):
    db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg", 1)

engine = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    return SessionLocal()
