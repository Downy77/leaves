from pathlib import Path

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader

from app.config import get_settings


def read_text_file(file_path: Path) -> str:
    settings = get_settings()
    suffix = file_path.suffix.lower()
    if suffix not in settings.supported_extensions:
        raise HTTPException(status_code=400, detail="Only .txt, .md, .pdf and .docx files are supported.")

    if suffix in {".txt", ".md"}:
        content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
    elif suffix == ".pdf":
        content = _read_pdf(file_path)
    else:
        content = _read_docx(file_path)

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    return content


def _read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    contents = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n".join(part for part in contents if part).strip()


def _read_docx(file_path: Path) -> str:
    document = Document(str(file_path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs).strip()
