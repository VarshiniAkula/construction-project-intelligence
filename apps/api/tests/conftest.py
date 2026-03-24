"""Test fixtures for BuildDocs AI API tests."""
import os
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up test environment
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.models.base import Base
from app.security.jwt import hash_password, create_access_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///test.db")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    os.remove("test.db") if os.path.exists("test.db") else None


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.rollback()
    sess.close()


@pytest.fixture
def seed_data(session):
    """Seed test users, project, memberships."""
    pw = hash_password("test123")

    session.execute(text("DELETE FROM project_memberships"))
    session.execute(text("DELETE FROM documents"))
    session.execute(text("DELETE FROM projects"))
    session.execute(text("DELETE FROM users"))
    session.commit()

    # Users
    session.execute(text(
        "INSERT INTO users (id, email, password_hash, full_name, is_active, is_superadmin, created_at, updated_at) "
        "VALUES ('u1', 'admin@test.com', :pw, 'Admin User', 1, 1, datetime('now'), datetime('now'))"
    ), {"pw": pw})
    session.execute(text(
        "INSERT INTO users (id, email, password_hash, full_name, is_active, is_superadmin, created_at, updated_at) "
        "VALUES ('u2', 'pm@test.com', :pw, 'PM User', 1, 0, datetime('now'), datetime('now'))"
    ), {"pw": pw})
    session.execute(text(
        "INSERT INTO users (id, email, password_hash, full_name, is_active, is_superadmin, created_at, updated_at) "
        "VALUES ('u3', 'sub@test.com', :pw, 'Sub User', 1, 0, datetime('now'), datetime('now'))"
    ), {"pw": pw})
    session.execute(text(
        "INSERT INTO users (id, email, password_hash, full_name, is_active, is_superadmin, created_at, updated_at) "
        "VALUES ('u4', 'owner@test.com', :pw, 'Owner User', 1, 0, datetime('now'), datetime('now'))"
    ), {"pw": pw})

    # Project
    session.execute(text(
        "INSERT INTO projects (id, name, code, created_at, updated_at) "
        "VALUES ('p1', 'Test Project', 'TP-001', datetime('now'), datetime('now'))"
    ))

    # Memberships
    session.execute(text(
        "INSERT INTO project_memberships (id, user_id, project_id, role, assigned_trade, created_at, updated_at) "
        "VALUES ('m1', 'u1', 'p1', 'admin', NULL, datetime('now'), datetime('now'))"
    ))
    session.execute(text(
        "INSERT INTO project_memberships (id, user_id, project_id, role, assigned_trade, created_at, updated_at) "
        "VALUES ('m2', 'u2', 'p1', 'project_manager', NULL, datetime('now'), datetime('now'))"
    ))
    session.execute(text(
        "INSERT INTO project_memberships (id, user_id, project_id, role, assigned_trade, created_at, updated_at) "
        "VALUES ('m3', 'u3', 'p1', 'subcontractor', 'electrical', datetime('now'), datetime('now'))"
    ))
    session.execute(text(
        "INSERT INTO project_memberships (id, user_id, project_id, role, assigned_trade, created_at, updated_at) "
        "VALUES ('m4', 'u4', 'p1', 'owner_viewer', NULL, datetime('now'), datetime('now'))"
    ))

    # Documents with different visibility
    docs = [
        ("d1", "project_full", None, "drawing"),
        ("d2", "field_team", None, "daily_report"),
        ("d3", "trade_scoped", "electrical", "submittal"),
        ("d4", "trade_scoped", "concrete", "submittal"),
        ("d5", "management_only", None, "general"),
        ("d6", "owner_shared", None, "general"),
    ]
    for doc_id, vis, trade, dtype in docs:
        session.execute(text(
            "INSERT INTO documents (id, project_id, uploaded_by_user_id, file_name, storage_key, "
            "file_type, doc_type, visibility_scope, trade_scope, status, created_at, updated_at) "
            "VALUES (:id, 'p1', 'u1', :fname, 'key', 'pdf', :dtype, :vis, :trade, 'ready', "
            "datetime('now'), datetime('now'))"
        ), {"id": doc_id, "fname": f"{doc_id}.pdf", "vis": vis, "trade": trade, "dtype": dtype})

    session.commit()

    return {
        "admin_token": create_access_token("u1"),
        "pm_token": create_access_token("u2"),
        "sub_token": create_access_token("u3"),
        "owner_token": create_access_token("u4"),
    }
