from fastapi import HTTPException
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import get_settings


def create_chat_model() -> ChatOpenAI:
    settings = get_settings()
    if not settings.llm_api_key:
        raise HTTPException(status_code=500, detail="Missing LLM_API_KEY in environment configuration.")

    return ChatOpenAI(
        model=settings.llm_model_name,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        streaming=True,
    )


def create_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    api_key = settings.embedding_api_key or settings.llm_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing EMBEDDING_API_KEY or LLM_API_KEY in environment configuration.")

    return OpenAIEmbeddings(
        model=settings.embedding_model_name,
        api_key=api_key,
        base_url=settings.embedding_base_url,
    )
