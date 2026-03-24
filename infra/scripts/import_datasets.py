#!/usr/bin/env python3
"""Import DATASETS folder into BuildDocs AI.

Reads the DATASETS directory structure, uploads each file to MinIO,
creates document records in the database, and dispatches Celery ingestion tasks.

Usage:
    python infra/scripts/import_datasets.py [--datasets-dir data/DATASETS] [--no-celery]
"""
import os
import sys
import uuid
import argparse
import mimetypes

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared", "python"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from minio import Minio

# ─── Folder-to-metadata mapping ──────────────────────────────────────────────

FOLDER_METADATA = {
    "Budget": {
        "doc_type": "change_order",
        "visibility_scope": "management_only",
        "trade_scope": None,
    },
    "Building Codes": {
        "doc_type": "specification",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Drawings/Architecture": {
        "doc_type": "drawing",
        "visibility_scope": "project_full",
        "trade_scope": "architecture",
    },
    "Drawings/MEP": {
        "doc_type": "drawing",
        "visibility_scope": "project_full",
        "trade_scope": "mep",
    },
    "Drawings/Structural": {
        "doc_type": "drawing",
        "visibility_scope": "project_full",
        "trade_scope": "structural",
    },
    "Inspections": {
        "doc_type": "daily_report",
        "visibility_scope": "field_team",
        "trade_scope": None,
    },
    "Project Overview/Geotechnical Report": {
        "doc_type": "general",
        "visibility_scope": "project_full",
        "trade_scope": "geotechnical",
    },
    "Project Overview/Owner-Architect Agreement": {
        "doc_type": "general",
        "visibility_scope": "owner_shared",
        "trade_scope": None,
    },
    "Project Overview/Permit Application": {
        "doc_type": "general",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Project Overview/RFQ": {
        "doc_type": "general",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Project Overview/Site Information": {
        "doc_type": "general",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "RFI": {
        "doc_type": "rfi",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Schedules/Schedule-Fabricated": {
        "doc_type": "general",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Schedules/Schedule Rules- AZ": {
        "doc_type": "specification",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
    "Submittal": {
        "doc_type": "submittal",
        "visibility_scope": "project_full",
        "trade_scope": None,
    },
}

# Inspection files have trade info in the filename
INSPECTION_TRADE_MAP = {
    "Foundation": "concrete",
    "Framing": "structural",
    "Electrical": "electrical",
    "Plumbing": "plumbing",
    "HVAC": "hvac",
    "Fire": "fire_protection",
    "Final_Inspection": None,
}

PROJECT_ID = "p-riverside-001"
UPLOADER_USER_ID = "u-pm-001"  # Sarah PM uploads all dataset files

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"}


def get_metadata_for_path(relative_path: str, filename: str) -> dict:
    """Determine doc_type, visibility_scope, trade_scope from folder path."""
    # Try longest matching prefix first
    sorted_folders = sorted(FOLDER_METADATA.keys(), key=len, reverse=True)
    for folder in sorted_folders:
        if relative_path.startswith(folder):
            meta = FOLDER_METADATA[folder].copy()

            # Special handling for inspection reports — derive trade from filename
            if folder == "Inspections" and filename.startswith("IR-"):
                for trade_key, trade_val in INSPECTION_TRADE_MAP.items():
                    if trade_key in filename:
                        meta["trade_scope"] = trade_val
                        break

            return meta

    return {"doc_type": "general", "visibility_scope": "project_full", "trade_scope": None}


def main():
    parser = argparse.ArgumentParser(description="Import DATASETS into BuildDocs AI")
    parser.add_argument("--datasets-dir", default=os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "DATASETS"))
    parser.add_argument("--no-celery", action="store_true",
                        help="Skip dispatching Celery tasks (just upload + create DB records)")
    parser.add_argument("--db-url", default=os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://builddocs:builddocs@localhost:5432/builddocs"))
    parser.add_argument("--minio-endpoint", default=os.environ.get("MINIO_ENDPOINT", "localhost:9000"))
    parser.add_argument("--minio-access-key", default=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"))
    parser.add_argument("--minio-secret-key", default=os.environ.get("MINIO_SECRET_KEY", "minioadmin"))
    parser.add_argument("--minio-bucket", default=os.environ.get("MINIO_BUCKET", "builddocs"))
    args = parser.parse_args()

    datasets_dir = os.path.abspath(args.datasets_dir)
    if not os.path.isdir(datasets_dir):
        print(f"Error: DATASETS directory not found: {datasets_dir}")
        sys.exit(1)

    # Connect to DB
    db_url = args.db_url
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Connect to MinIO
    minio_client = Minio(
        args.minio_endpoint,
        access_key=args.minio_access_key,
        secret_key=args.minio_secret_key,
        secure=False,
    )
    bucket = args.minio_bucket
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

    # Celery
    celery_app = None
    if not args.no_celery:
        try:
            from celery import Celery
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            celery_app = Celery(broker=redis_url)
        except ImportError:
            print("Warning: celery not installed, skipping task dispatch")

    # Walk DATASETS directory
    imported = 0
    skipped = 0

    for root, dirs, files in os.walk(datasets_dir):
        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                skipped += 1
                continue

            # Compute relative path from DATASETS root
            rel_dir = os.path.relpath(root, datasets_dir)
            if rel_dir == ".":
                rel_dir = ""

            meta = get_metadata_for_path(rel_dir, filename)

            doc_id = str(uuid.uuid4())
            file_type = ext.lstrip(".")
            storage_key = f"projects/{PROJECT_ID}/documents/{doc_id}/original{ext}"

            # Upload to MinIO
            file_size = os.path.getsize(filepath)
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            print(f"  Uploading: {rel_dir}/{filename} ({file_size // 1024}KB) → {meta['doc_type']}/{meta['visibility_scope']}")

            with open(filepath, "rb") as f:
                minio_client.put_object(
                    bucket, storage_key, f, file_size,
                    content_type=content_type,
                )

            # Create document record
            session.execute(text(
                """INSERT INTO documents
                   (id, project_id, uploaded_by_user_id, file_name, storage_key,
                    file_type, doc_type, visibility_scope, trade_scope, revision,
                    status, page_count, created_at, updated_at)
                   VALUES (:id, :project_id, :uploader, :file_name, :storage_key,
                           :file_type, :doc_type, :vis, :trade, NULL,
                           'processing', 0, NOW(), NOW())"""
            ), {
                "id": doc_id,
                "project_id": PROJECT_ID,
                "uploader": UPLOADER_USER_ID,
                "file_name": filename,
                "storage_key": storage_key,
                "file_type": file_type,
                "doc_type": meta["doc_type"],
                "vis": meta["visibility_scope"],
                "trade": meta["trade_scope"],
            })

            # Dispatch Celery task
            if celery_app:
                celery_app.send_task(
                    "worker.tasks.ingest.ingest_document",
                    args=[doc_id],
                )

            imported += 1

    session.commit()
    session.close()

    print(f"\nImport complete: {imported} documents imported, {skipped} files skipped")
    if not celery_app:
        print("Note: Celery tasks were not dispatched. Run the worker to process documents,")
        print("  or re-run with Celery available to dispatch ingestion tasks.")
    print("\nDocument breakdown by category:")

    # Summary
    counts = {}
    for root, dirs, files in os.walk(datasets_dir):
        rel = os.path.relpath(root, datasets_dir)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                cat = rel.split("/")[0] if rel != "." else "root"
                counts[cat] = counts.get(cat, 0) + 1
    for cat, count in sorted(counts.items()):
        print(f"  {cat}: {count} files")


if __name__ == "__main__":
    main()
