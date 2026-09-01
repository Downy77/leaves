from collections.abc import Iterable


def build_general_answer(question: str) -> str:
    normalized = question.strip()
    lower_question = normalized.lower()

    if _contains_any(lower_question, ("你好", "hello", "hi", "hey")):
        return "你好，我可以回答普通问题，也可以切换到知识库检索模式基于已上传文档作答。"

    if _contains_any(lower_question, ("你是谁", "who are you")):
        return "我是这个项目里的普通问答助手。当前版本支持普通问答和知识库检索两种模式。"

    if _contains_any(lower_question, ("支持", "功能", "capability", "feature")):
        return (
            "当前系统支持两种问答方式：\n"
            "1. 普通问答：不依赖知识库，适合通用咨询。\n"
            "2. 知识库检索：基于你上传的文档返回相关片段和答案摘要。"
        )

    if _contains_any(lower_question, ("fastapi", "vue", "技术栈", "stack")):
        return (
            "这个项目当前采用 FastAPI 作为后端接口服务，Vue 3 + Vite 作为前端页面。\n"
            "后端负责文档上传、解析、检索和问答接口，前端负责登录、会话管理和对话展示。"
        )

    return (
        f"这是普通问答模式下对问题“{normalized}”的回答。\n"
        "当前版本的普通问答是本地基础实现，适合演示双模式流程。\n"
        "如果你希望更强的开放式问答能力，可以继续接入大模型 API。"
    )


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)
