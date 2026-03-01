from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet | None:
    key = (settings.FILE_ENCRYPTION_KEY or "").strip()
    if not key:
        return None
    return Fernet(key.encode("utf-8"))


def project_root(project_id: str) -> Path:
    root = Path(settings.STORAGE_PATH).expanduser().resolve()
    return root / "projects" / project_id


def ensure_project_dirs(project_id: str) -> None:
    (project_root(project_id) / "documents").mkdir(parents=True, exist_ok=True)
    (project_root(project_id) / "index").mkdir(parents=True, exist_ok=True)


def document_path(project_id: str, document_id: str, version: int, stored_filename: str) -> Path:
    return project_root(project_id) / "documents" / document_id / f"v{version}" / stored_filename


def save_document_bytes(
    project_id: str,
    document_id: str,
    version: int,
    stored_filename: str,
    data: bytes,
) -> Tuple[str, str, Path]:
    '''
    Saves bytes to disk, optionally encrypted at rest.
    Returns (sha256_hex, storage_mode, path)
    '''
    ensure_project_dirs(project_id)
    path = document_path(project_id, document_id, version, stored_filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    sha256_hex = hashlib.sha256(data).hexdigest()

    f = _fernet()
    if f:
        data = f.encrypt(data)
        mode = "encrypted"
    else:
        mode = "plain"

    path.write_bytes(data)
    return sha256_hex, mode, path


def read_document_bytes(project_id: str, document_id: str, version: int, stored_filename: str) -> bytes:
    path = document_path(project_id, document_id, version, stored_filename)
    data = path.read_bytes()
    f = _fernet()
    if not f:
        return data
    try:
        return f.decrypt(data)
    except InvalidToken:
        # If the key changed, decryption fails.
        raise RuntimeError("File decryption failed. Check FILE_ENCRYPTION_KEY.")


def delete_project_index(project_id: str) -> None:
    idx = project_root(project_id) / "index"
    if idx.exists():
        for p in idx.glob("*"):
            try:
                if p.is_file():
                    p.unlink()
            except Exception:
                pass
