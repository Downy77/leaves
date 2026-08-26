from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.models import AskRequest, AskResponse
from app.services.qa_service import qa_service
from app.services.qa_stream import qa_stream_service
from app.services.storage import metadata_store


router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    return qa_service.ask(payload)


@router.post("/ask/stream")
async def ask_question_stream(payload: AskRequest):
    if payload.mode == "knowledge_base" and not metadata_store.list_documents():
        raise HTTPException(status_code=400, detail="Knowledge base is empty. Please upload documents first.")

    def event_stream():
        matches = qa_stream_service.build_matches(payload.question, payload.top_k) if payload.mode == "knowledge_base" else []
        metadata = {
            "mode": payload.mode,
            "answer_source": "knowledge_base" if payload.mode == "knowledge_base" else "general_assistant",
            "matches": [item.model_dump() for item in matches],
        }
        yield f"event: meta\ndata: {json.dumps(metadata, ensure_ascii=False)}\n\n"
        for chunk in qa_stream_service.stream_answer(payload):
            yield f"event: token\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
