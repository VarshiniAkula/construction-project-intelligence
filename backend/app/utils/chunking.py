from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    chunk_index: int


def chunk_text(text: str, *, max_chars: int = 1200, overlap: int = 150) -> list[TextChunk]:
    '''
    Simple character-based chunker good enough for an MVP.
    '''
    text = (text or "").strip()
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    i = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk, chunk_index=i))
            i += 1
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks
