"""Storage client for the worker — supports local filesystem or MinIO."""
import os
import io
from pathlib import Path

_minio_client = None


def _storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "local")


def _local_dir() -> Path:
    p = Path(os.environ.get("STORAGE_LOCAL_DIR", "./storage"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_minio():
    from minio import Minio
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            os.environ.get("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.environ.get("MINIO_USE_SSL", "false").lower() == "true",
        )
    return _minio_client


def get_bucket() -> str:
    return os.environ.get("MINIO_BUCKET", "builddocs")


def download_bytes(storage_key: str) -> bytes:
    if _storage_backend() == "local":
        return (_local_dir() / storage_key).read_bytes()
    client = _get_minio()
    response = client.get_object(get_bucket(), storage_key)
    data = response.read()
    response.close()
    response.release_conn()
    return data


def upload_bytes(storage_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    if _storage_backend() == "local":
        path = _local_dir() / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return
    client = _get_minio()
    client.put_object(get_bucket(), storage_key, io.BytesIO(data), len(data), content_type=content_type)
