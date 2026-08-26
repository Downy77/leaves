# FastAPI Knowledge Base QA

一个基于 `FastAPI + Vue 3 + LangChain + Chroma + LangSmith` 的知识库问答项目，支持文件上传、知识库检索问答、普通问答、Tracing 和测试。

## 技术栈

- 后端：FastAPI
- 前端：Vue 3 + Vite
- 编排与链路：LangChain
- 向量库：Chroma
- 模型接入：OpenAI-compatible API
- Tracing / Observability：LangSmith

## 功能

- 上传 `.txt`、`.md`、`.pdf`、`.docx` 文档
- 使用 LangChain 文本切分器自动分块
- 使用 Chroma 本地持久化向量库
- 知识库检索问答
- 普通问答
- Vue 3 可视化界面
- `.env` 配置模型 Key、模型名、Base URL 和检索参数
- LangSmith tracing 配置
- pytest 测试骨架

## 项目结构

```text
.
├── app
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── routers
│   │   ├── documents.py
│   │   └── qa.py
│   └── services
│       ├── document_service.py
│       ├── langchain_factory.py
│       ├── parser.py
│       ├── qa_service.py
│       ├── storage.py
│       └── vector_store.py
├── frontend
│   ├── src
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── tests
│   ├── conftest.py
│   ├── test_health.py
│   └── test_qa_contract.py
├── .env
├── .env.example
├── .gitignore
├── pytest.ini
├── main.py
└── requirements.txt
```

## 环境配置

`.env` 中除了模型配置外，新增了 LangSmith 配置：

```env
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=knowledge-base-qa
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

启用 tracing 时改成：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=knowledge-base-qa
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## 安装依赖

后端：

```bash
pip install -r requirements.txt
```

前端：

```bash
cd frontend
npm install
```

## 启动方式

启动后端：

```bash
uvicorn app.main:app --reload
```

启动前端开发环境：

```bash
cd frontend
npm run dev
```

## 接口说明

### 上传文档

- `POST /documents/upload`

### 文档列表

- `GET /documents`

### 问答

- `POST /qa/ask`

请求体示例：

```json
{
  "question": "这个项目支持哪些文件格式？",
  "top_k": 3,
  "mode": "knowledge_base"
}
```

`mode` 可选值：

- `knowledge_base`
- `general`

## LangSmith

当前项目已在关键链路上接入 LangSmith：

- 文档上传入库
- 普通问答
- 知识库问答

启用后，这些 LangChain 调用和 `@traceable` 标记的方法会进入 LangSmith。

## 测试

运行：

```bash
pytest
```

当前测试覆盖：

- `/health` 健康检查
- `/qa/ask` 普通问答接口契约
- `/qa/ask` 知识库问答接口契约
