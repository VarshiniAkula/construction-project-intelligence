#!/usr/bin/env python3
"""Seed script for BuildDocs AI demo data."""
import os
import sys

# Add API app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "python"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.security.jwt import hash_password

# Use sync driver for seeding
db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    db_url = os.environ.get("DATABASE_URL_SYNC", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
if "asyncpg" in db_url:
    db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg")

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)


def seed():
    session = Session()

    # Check if already seeded
    result = session.execute(text("SELECT COUNT(*) FROM users"))
    if result.scalar() > 0:
        print("Database already seeded. Skipping.")
        session.close()
        return

    password_hash = hash_password("builddocs123")

    users = [
        {
            "id": "u-admin-001",
            "email": "admin@builddocs.ai",
            "password_hash": password_hash,
            "full_name": "Alex Chen",
            "company_name": "BuildDocs AI",
            "is_active": True,
            "is_superadmin": True,
        },
        {
            "id": "u-pm-001",
            "email": "sarah.pm@example.com",
            "password_hash": password_hash,
            "full_name": "Sarah Martinez",
            "company_name": "Riverside Development Corp",
            "is_active": True,
            "is_superadmin": False,
        },
        {
            "id": "u-super-001",
            "email": "mike.super@example.com",
            "password_hash": password_hash,
            "full_name": "Mike Thompson",
            "company_name": "Riverside Development Corp",
            "is_active": True,
            "is_superadmin": False,
        },
        {
            "id": "u-sub-001",
            "email": "jose.electrical@example.com",
            "password_hash": password_hash,
            "full_name": "Jose Rivera",
            "company_name": "Rivera Electrical LLC",
            "is_active": True,
            "is_superadmin": False,
        },
        {
            "id": "u-owner-001",
            "email": "owner@riverside.com",
            "password_hash": password_hash,
            "full_name": "Patricia Riverside",
            "company_name": "Riverside Holdings",
            "is_active": True,
            "is_superadmin": False,
        },
    ]

    for u in users:
        session.execute(text(
            """INSERT INTO users (id, email, password_hash, full_name, company_name, is_active, is_superadmin, created_at, updated_at)
               VALUES (:id, :email, :password_hash, :full_name, :company_name, :is_active, :is_superadmin, NOW(), NOW())"""
        ), u)

    session.execute(text(
        """INSERT INTO projects (id, name, code, location, description, created_at, updated_at)
           VALUES ('p-riverside-001', 'Riverside Commercial Complex', 'RCC-2025',
                   'Portland, OR', 'Mixed-use commercial development with retail, office, and parking. 5 stories, 180,000 SF.', NOW(), NOW())"""
    ))

    memberships = [
        {"id": "m-001", "user_id": "u-admin-001", "project_id": "p-riverside-001", "role": "admin", "assigned_trade": None},
        {"id": "m-002", "user_id": "u-pm-001", "project_id": "p-riverside-001", "role": "project_manager", "assigned_trade": None},
        {"id": "m-003", "user_id": "u-super-001", "project_id": "p-riverside-001", "role": "superintendent", "assigned_trade": None},
        {"id": "m-004", "user_id": "u-sub-001", "project_id": "p-riverside-001", "role": "subcontractor", "assigned_trade": "electrical"},
        {"id": "m-005", "user_id": "u-owner-001", "project_id": "p-riverside-001", "role": "owner_viewer", "assigned_trade": None},
    ]

    for m in memberships:
        session.execute(text(
            """INSERT INTO project_memberships (id, user_id, project_id, role, assigned_trade, created_at, updated_at)
               VALUES (:id, :user_id, :project_id, :role, :assigned_trade, NOW(), NOW())"""
        ), m)

    session.commit()
    session.close()
    print("Seed data created successfully!")
    print("\nDemo accounts (password: builddocs123):")
    print("  admin@builddocs.ai          - Admin")
    print("  sarah.pm@example.com         - Project Manager")
    print("  mike.super@example.com       - Superintendent")
    print("  jose.electrical@example.com  - Subcontractor (Electrical)")
    print("  owner@riverside.com          - Owner / Viewer")


if __name__ == "__main__":
    seed()
