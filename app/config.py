from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Knowledge Base QA"
    app_version: str = "2.0.0"
    api_prefix: str = ""

    data_dir: Path = BASE_DIR / "data"
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    chroma_dir: Path = BASE_DIR / "data" / "chroma"
    metadata_file: Path = BASE_DIR / "data" / "documents.json"

    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_top_k: int = 4

    llm_provider: str = Field(default="openai_compatible")
    llm_api_key: str = Field(default="")
    llm_base_url: str = Field(default="https://api.openai.com/v1")
    llm_model_name: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.2)

    embedding_provider: str = Field(default="openai_compatible")
    embedding_api_key: str = Field(default="")
    embedding_base_url: str = Field(default="https://api.openai.com/v1")
    embedding_model_name: str = Field(default="text-embedding-3-small")

    langsmith_tracing: bool = Field(default=False)
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = Field(default="knowledge-base-qa")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com")

    supported_extensions: set[str] = {".txt", ".md", ".pdf", ".docx"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return settings
