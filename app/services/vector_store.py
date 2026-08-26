from langchain_chroma import Chroma

from app.config import get_settings
from app.services.langchain_factory import create_embeddings


COLLECTION_NAME = "knowledge_documents"


def get_vector_store() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=create_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )
