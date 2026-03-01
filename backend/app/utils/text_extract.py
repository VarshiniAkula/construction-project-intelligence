from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from docx import Document as DocxDocument


def extract_text_from_bytes(filename: str, data: bytes, content_type: str | None = None) -> str:
    '''
    Best-effort text extraction for common construction documents:
    - PDF (specs, RFIs exported to PDF, reports)
    - DOCX (meeting notes, RFI logs)
    - TXT/CSV
    '''
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    # PDF
    if name.endswith(".pdf") or "pdf" in ctype:
        reader = PdfReader(BytesIO(data))
        texts: list[str] = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t:
                texts.append(t)
        return "\n\n".join(texts).strip()

    # DOCX
    if name.endswith(".docx") or "word" in ctype:
        doc = DocxDocument(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs]).strip()

    # Plain text (best effort)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1")
        except Exception:
            return ""
