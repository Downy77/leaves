from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

from app.config import get_settings
from app.models import StoredDocument
from app.services.parser import read_text_file
from app.services.storage import metadata_store
from app.services.vector_store import get_vector_store


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def list_documents(self) -> list[StoredDocument]:
        return metadata_store.list_documents()

    @traceable(name="document_service.save_upload", run_type="chain")
    def save_upload(self, filename: str, file_bytes: bytes) -> StoredDocument:
        suffix = Path(filename).suffix.lower()
        document_id = str(uuid4())
        target_path = self.settings.upload_dir / f"{document_id}{suffix}"
        target_path.write_bytes(file_bytes)

        text = read_text_file(target_path)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = splitter.split_text(text)

        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "chunk_id": f"{document_id}-{index}",
                    "document_id": document_id,
                    "filename": filename,
                },
            )
            for index, chunk in enumerate(chunks, start=1)
        ]

        vector_store = get_vector_store()
        vector_store.add_documents(documents)

        stored_document = StoredDocument(
            document_id=document_id,
            filename=filename,
            file_path=str(target_path),
            chunk_count=len(documents),
        )
        metadata_store.add_document(stored_document)
        return stored_document


document_service = DocumentService()
