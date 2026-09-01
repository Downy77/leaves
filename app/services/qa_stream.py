from collections.abc import Iterator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch

from app.config import get_settings
from app.models import AskRequest, RetrievedChunk
from app.services.langchain_factory import create_chat_model
from app.services.vector_store import get_vector_store


class QAStreamService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_matches(self, question: str, top_k: int) -> list[RetrievedChunk]:
        vector_store = get_vector_store()
        search_kwargs = {
            "k": min(top_k, self.settings.retrieval_top_k if top_k > self.settings.retrieval_top_k else top_k)
        }
        results = vector_store.similarity_search_with_relevance_scores(question, **search_kwargs)

        return [
            RetrievedChunk(
                chunk_id=document.metadata.get("chunk_id", ""),
                document_id=document.metadata.get("document_id", ""),
                filename=document.metadata.get("filename", "unknown"),
                content=document.page_content,
                score=score,
            )
            for document, score in results
        ]

    def build_web_context(self, question: str) -> str:
        if not self.settings.tavily_api_key:
            return ""

        try:
            tool = TavilySearch(
                tavily_api_key=self.settings.tavily_api_key,
                max_results=self.settings.tavily_max_results,
                topic="general",
                search_depth="advanced",
                include_answer=True,
            )
            result = tool.invoke({"query": question})
        except Exception:
            return ""

        if isinstance(result, str):
            return result.strip()

        if not isinstance(result, dict):
            return ""

        results = result.get("results", [])
        answer = result.get("answer")
        lines: list[str] = []

        if answer:
            lines.append(f"联网检索摘要：{answer}")

        for index, item in enumerate(results, start=1):
            title = item.get("title") or item.get("url") or f"来源 {index}"
            content = item.get("content") or item.get("raw_content") or ""
            url = item.get("url") or ""
            snippet = content.strip().replace("\n", " ")
            if len(snippet) > 260:
                snippet = f"{snippet[:260]}..."
            line = f"{index}. {title}"
            if url:
                line = f"{line} ({url})"
            if snippet:
                line = f"{line}\n   {snippet}"
            lines.append(line)

        return "\n\n".join(lines)

    def _build_general_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个带联网搜索能力的问答助手。"
                    "你需要优先参考给定的联网检索结果来回答问题。"
                    "如果检索结果不足以支撑结论，要明确说明，并避免编造。"
                    "回答请使用中文，除非用户明确要求其他语言。"
                    "如果提供了联网检索结果，请结合结果内容给出简洁、可靠的回答，并适当提及来源。",
                ),
                ("system", "联网检索结果：\n{web_context}"),
                ("human", "{question}"),
            ]
        )
        return prompt | create_chat_model() | StrOutputParser()

    def _build_kb_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是知识库问答助手。你只能基于提供的知识库内容回答问题。"
                    "如果知识库内容不足以支持结论，明确说明不知道，并建议补充文档。"
                    "回答使用中文，结构清晰，必要时引用来源文件名。",
                ),
                (
                    "human",
                    "问题：{question}\n\n知识库内容：\n{context}\n\n请基于以上内容回答。",
                ),
            ]
        )
        return prompt | create_chat_model() | StrOutputParser()

    def stream_answer(
        self,
        payload: AskRequest,
        matches: list[RetrievedChunk] | None = None,
    ) -> Iterator[str]:
        if payload.mode == "general":
            web_context = self.build_web_context(payload.question)
            chain = self._build_general_chain()
            for chunk in chain.stream({"question": payload.question, "web_context": web_context or "无"}):
                yield chunk
            return

        matches = matches or self.build_matches(payload.question, payload.top_k)
        if not matches:
            yield (
                f"没有在知识库中找到与问题“{payload.question}”足够相关的内容。"
                "请尝试换一种问法，或者先上传更相关的文档。"
            )
            return

        context = "\n\n".join(
            f"来源文件：{item.filename}\n片段内容：{item.content}" for item in matches
        )
        chain = self._build_kb_chain()
        for chunk in chain.stream({"question": payload.question, "context": context}):
            yield chunk


qa_stream_service = QAStreamService()
