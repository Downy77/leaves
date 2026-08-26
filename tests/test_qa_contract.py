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
