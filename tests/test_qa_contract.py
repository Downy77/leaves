from unittest.mock import patch

from app.models import AskResponse, RetrievedChunk


def test_general_qa_contract(client):
    mocked_response = AskResponse(
        answer="这是一个测试回答。",
        matches=[],
        mode="general",
        answer_source="general_assistant",
    )

    with patch("app.routers.qa.qa_service.ask", return_value=mocked_response):
        response = client.post(
            "/qa/ask",
            json={
                "question": "测试普通问答",
                "top_k": 3,
                "mode": "general",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "general"
    assert payload["answer_source"] == "general_assistant"
    assert payload["matches"] == []


def test_knowledge_base_qa_contract(client):
    mocked_response = AskResponse(
        answer="这是一个知识库测试回答。",
        matches=[
            RetrievedChunk(
                chunk_id="doc-1-1",
                document_id="doc-1",
                filename="sample.txt",
                content="测试片段",
                score=0.95,
            )
        ],
        mode="knowledge_base",
        answer_source="knowledge_base",
    )

    with patch("app.routers.qa.qa_service.ask", return_value=mocked_response):
        response = client.post(
            "/qa/ask",
            json={
                "question": "测试知识库问答",
                "top_k": 3,
                "mode": "knowledge_base",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "knowledge_base"
    assert payload["answer_source"] == "knowledge_base"
    assert len(payload["matches"]) == 1


def test_general_web_search_context_building(monkeypatch):
    from importlib import reload

    from app.services import qa_stream as qa_stream_module

    qa_stream_module = reload(qa_stream_module)
    qa_stream_service = qa_stream_module.qa_stream_service

    monkeypatch.setattr(qa_stream_service.settings, "tavily_api_key", "test-key")
    monkeypatch.setattr(qa_stream_service.settings, "tavily_max_results", 2)

    class DummyTavilySearch:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def invoke(self, payload):
            assert "OpenAI" in payload["query"]
            return {
                "answer": "OpenAI 发布了新功能。",
                "results": [
                    {
                        "title": "OpenAI News",
                        "url": "https://example.com/openai-news",
                        "content": "OpenAI 发布了新的模型和产品更新。",
                    }
                ],
            }

    with patch.object(qa_stream_module, "TavilySearch", DummyTavilySearch):
        context = qa_stream_service.build_web_context("今天 OpenAI 有什么新消息")

    assert context
    assert "联网检索摘要" in context
    assert "OpenAI News" in context
    assert "https://example.com/openai-news" in context
