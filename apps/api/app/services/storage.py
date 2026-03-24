"""Storage service — supports local filesystem or Supabase Storage."""
import io
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

# ── Local filesystem backend ──────────────────────────────

def _local_dir() -> Path:
    p = Path(settings.STORAGE_LOCAL_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _local_upload(storage_key: str, data: bytes, content_type: str = "") -> str:
    path = _local_dir() / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return storage_key


def _local_download(storage_key: str) -> bytes:
    return (_local_dir() / storage_key).read_bytes()


def _local_delete(storage_key: str) -> None:
    path = _local_dir() / storage_key
    if path.exists():
        path.unlink()


def _local_presigned_url(storage_key: str, **_) -> str:
    return f"/storage/{storage_key}"


# ── Supabase Storage backend ──────────────────────────────

def _supabase_upload(storage_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    import httpx
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Content-Type": content_type,
    }
    # Upsert (overwrite if exists)
    resp = httpx.put(url, content=data, headers=headers, timeout=120)
    if resp.status_code not in (200, 201):
        # Try POST for new files
        resp = httpx.post(url, content=data, headers=headers, timeout=120)
    if resp.status_code not in (200, 201):
        logger.error(f"Supabase upload failed: {resp.status_code} {resp.text}")
    return storage_key


def _supabase_download(storage_key: str) -> bytes:
    import httpx
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
    }
    resp = httpx.get(url, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.content


def _supabase_delete(storage_key: str) -> None:
    import httpx
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
    }
    httpx.delete(url, json={"prefixes": [storage_key]}, headers=headers, timeout=30)


def _supabase_presigned_url(storage_key: str, **_) -> str:
    return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"


# ── Public API (dispatches based on STORAGE_BACKEND) ──────

def upload_file(storage_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    if settings.STORAGE_BACKEND == "local":
        return _local_upload(storage_key, data, content_type)
    return _supabase_upload(storage_key, data, content_type)


def download_file(storage_key: str) -> bytes:
    if settings.STORAGE_BACKEND == "local":
        return _local_download(storage_key)
    return _supabase_download(storage_key)


def get_presigned_url(storage_key: str, expires_hours: int = 1) -> str:
    if settings.STORAGE_BACKEND == "local":
        return _local_presigned_url(storage_key)
    return _supabase_presigned_url(storage_key)


def delete_file(storage_key: str) -> None:
    if settings.STORAGE_BACKEND == "local":
        return _local_delete(storage_key)
    return _supabase_delete(storage_key)
