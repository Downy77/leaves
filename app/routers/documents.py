from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models import DocumentListResponse, UploadResponse
from app.services.document_service import document_service


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=document_service.list_documents())


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.supported_extensions:
        raise HTTPException(status_code=400, detail="Only .txt, .md, .pdf and .docx files are supported.")

    file_bytes = await file.read()
    stored_document = document_service.save_upload(file.filename or f"document{suffix}", file_bytes)
    return UploadResponse(
        document_id=stored_document.document_id,
        filename=stored_document.filename,
        chunk_count=stored_document.chunk_count,
    )
