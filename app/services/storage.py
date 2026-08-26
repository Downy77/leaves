import json

from app.config import get_settings
from app.models import StoredDocument


class MetadataStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.metadata_file = settings.metadata_file
        self._ensure_metadata_file()

    def _ensure_metadata_file(self) -> None:
        if not self.metadata_file.exists():
            self.metadata_file.write_text(
                json.dumps({"documents": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def list_documents(self) -> list[StoredDocument]:
        payload = json.loads(self.metadata_file.read_text(encoding="utf-8"))
        return [StoredDocument(**item) for item in payload["documents"]]

    def add_document(self, document: StoredDocument) -> None:
        documents = self.list_documents()
        documents.append(document)
        self.metadata_file.write_text(
            json.dumps({"documents": [item.model_dump() for item in documents]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


metadata_store = MetadataStore()
