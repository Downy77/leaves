from typing import Literal

from pydantic import BaseModel, Field


class StoredDocument(BaseModel):
    document_id: str
    filename: str
    file_path: str
    chunk_count: int


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    message: str = "Document uploaded and indexed successfully."


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question.")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of retrieved chunks.")
    mode: Literal["knowledge_base", "general"] = Field(
        default="knowledge_base",
        description="Question answering mode.",
    )
    stream: bool = Field(default=False, description="Whether to stream the answer.")


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    score: float | None = None


class AskResponse(BaseModel):
    answer: str
    matches: list[RetrievedChunk]
    mode: Literal["knowledge_base", "general"]
    answer_source: Literal["knowledge_base", "general_assistant"]


class DocumentListResponse(BaseModel):
    documents: list[StoredDocument]
