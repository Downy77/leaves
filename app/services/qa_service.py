from langsmith import traceable

from app.models import AskRequest, AskResponse, RetrievedChunk
from app.services.qa_stream import qa_stream_service


class QAService:
    @traceable(name="qa_service.ask", run_type="chain")
    def ask(self, payload: AskRequest) -> AskResponse:
        stream_iter = qa_stream_service.stream_answer(payload)
        answer = "".join(stream_iter)
        matches = []
        if payload.mode == "knowledge_base":
            matches = qa_stream_service.build_matches(payload.question, payload.top_k)
            answer_source = "knowledge_base"
        else:
            answer_source = "general_assistant"
        return AskResponse(
            answer=answer,
            matches=matches,
            mode=payload.mode,
            answer_source=answer_source,
        )


qa_service = QAService()
