from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from app.models import AskRequest, AskResponse
from app.services.langchain_factory import create_chat_model
from app.services.qa_stream import qa_stream_service


class QAService:
    @traceable(name="qa_service.ask", run_type="chain")
    def ask(self, payload: AskRequest) -> AskResponse:
        answer = "".join(qa_stream_service.stream_answer(payload))
        if payload.mode == "knowledge_base":
            matches = qa_stream_service.build_matches(payload.question, payload.top_k)
            answer_source = "knowledge_base"
        else:
            matches = []
            answer_source = "general_assistant"

        return AskResponse(
            answer=answer,
            matches=matches,
            mode=payload.mode,
            answer_source=answer_source,
        )

    @traceable(name="qa_service.generate_title", run_type="llm")
    def generate_title(self, question: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个对话标题生成器。"
                    "请根据用户的第一个问题生成一个简短中文标题，要求 6 到 14 个汉字。"
                    "不要使用标点、引号、句号、冒号、书名号、表情或多余说明。"
                    "只输出标题本身。",
                ),
                ("human", "{question}"),
            ]
        )
        chain = prompt | create_chat_model() | StrOutputParser()
        title = chain.invoke({"question": question}).strip()
        title = title.replace("\n", " ").replace("\r", " ").strip(" \"'`")
        return title or "新对话"


qa_service = QAService()
