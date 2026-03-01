from __future__ import annotations

import json
import pickle
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.storage import project_root


CHUNKS_FILE = "chunks.jsonl"
INDEX_FILE = "tfidf.pkl"


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    version: int
    text: str
    score: float


def _index_dir(project_id: str) -> Path:
    return project_root(project_id) / "index"


def _chunks_path(project_id: str) -> Path:
    return _index_dir(project_id) / CHUNKS_FILE


def _index_path(project_id: str) -> Path:
    return _index_dir(project_id) / INDEX_FILE


class ProjectVectorStore:
    '''
    MVP vector store:
    - Stores chunks on disk (JSONL)
    - Builds a TF-IDF index (pickle) for similarity search
    '''
    def add_chunks(self, project_id: str, *, document_id: str, filename: str, version: int, chunks: list[str]) -> int:
        _index_dir(project_id).mkdir(parents=True, exist_ok=True)
        p = _chunks_path(project_id)
        added = 0
        with p.open("a", encoding="utf-8") as f:
            for c in chunks:
                rec = {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "filename": filename,
                    "version": int(version),
                    "text": c,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                added += 1
        self.rebuild(project_id)
        return added

    def rebuild(self, project_id: str) -> None:
        p = _chunks_path(project_id)
        if not p.exists():
            return
        rows: list[dict[str, Any]] = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        if not rows:
            return

        texts = [r.get("text", "") for r in rows]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=60000)
        matrix = vectorizer.fit_transform(texts)  # sparse
        payload = {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "meta": [
                {
                    "document_id": r.get("document_id"),
                    "filename": r.get("filename"),
                    "version": r.get("version"),
                    "text": r.get("text"),
                }
                for r in rows
            ],
        }
        _index_path(project_id).write_bytes(pickle.dumps(payload))

    def search(self, project_id: str, query: str, *, k: int = 5) -> list[RetrievedChunk]:
        ip = _index_path(project_id)
        if not ip.exists():
            return []
        payload = pickle.loads(ip.read_bytes())
        vectorizer: TfidfVectorizer = payload["vectorizer"]
        matrix = payload["matrix"]
        meta = payload["meta"]

        q = (query or "").strip()
        if not q:
            return []

        qvec = vectorizer.transform([q])
        # TF-IDF vectors are L2-normalized by default, so dot product approximates cosine similarity.
        scores = (matrix @ qvec.T).toarray().ravel()
        if scores.size == 0:
            return []
        top_idx = np.argsort(-scores)[:k]
        out: list[RetrievedChunk] = []
        for i in top_idx:
            m = meta[int(i)]
            out.append(
                RetrievedChunk(
                    document_id=m["document_id"],
                    filename=m["filename"],
                    version=int(m.get("version") or 1),
                    text=m["text"],
                    score=float(scores[int(i)]),
                )
            )
        return out


vectorstore = ProjectVectorStore()
