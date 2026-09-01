# FastAPI Knowledge Base QA

一个基于 `FastAPI + Vue 3 + LangChain + Chroma + MySQL + LangSmith` 的知识库问答项目，支持：

- 文件上传与知识库索引
- 普通问答
- 知识库检索问答
- 用户登录与 JWT 认证
- 按用户隔离的会话和聊天记录持久化
- LangSmith trace / test

## 技术栈

- 后端：FastAPI
- 前端：Vue 3 + Vite + Element Plus
- 编排与链路：LangChain
- 向量库：Chroma
- 用户与会话存储：MySQL + SQLAlchemy
- 观测：LangSmith

## 主要功能

- 上传 `.txt`、`.md`、`.pdf`、`.docx` 文档
- 自动切分文本并构建知识库索引
- 知识库检索问答
- 普通问答
- 用户注册、登录、鉴权
- 会话列表、聊天记录按用户账号独立保存
- 普通问答支持多会话
- 首条消息自动生成会话标题
- Vue 3 前端分入口展示普通问答、知识库问答和索引创建

## 项目结构

```text
.
├─ app
│  ├─ config.py
│  ├─ db.py
│  ├─ deps.py
│  ├─ main.py
│  ├─ models.py
│  ├─ orm_models.py
│  ├─ routers
│  │  ├─ auth.py
│  │  ├─ chat.py
│  │  ├─ documents.py
│  │  └─ qa.py
│  └─ services
│     ├─ auth_service.py
│     ├─ chat_service.py
│     ├─ document_service.py
│     ├─ general_qa.py
│     ├─ langchain_factory.py
│     ├─ parser.py
│     ├─ qa_service.py
│     ├─ qa_stream.py
│     ├─ retriever.py
│     ├─ storage.py
│     └─ vector_store.py
├─ frontend
│  ├─ src
│  ├─ package.json
│  └─ vite.config.js
├─ tests
├─ .env
├─ .env.example
├─ main.py
└─ requirements.txt
```

## 环境变量

项目根目录已经提供 `.env.example`，你只需要复制一份为 `.env` 并填写 key 即可。

### 需要配置的核心项

```env
# LLM
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
LLM_TEMPERATURE=0.2

# Embedding
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_KEY=your_embedding_key_here
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL_NAME=text-embedding-3-small

# LangSmith
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=knowledge-base-qa
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# MySQL
MYSQL_URL=mysql+pymysql://root:password@127.0.0.1:3306/knowledge_base_qa?charset=utf8mb4

# If your MySQL server uses caching_sha2_password or sha256_password,
# keep the cryptography dependency installed.

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
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

后端：

```bash
uvicorn app.main:app --reload
```

如果你要先手动建表，可以直接执行：

```bash
.venv\Scripts\python.exe scripts\create_tables.py
```

或者把 `scripts/mysql_schema.sql` 交给 MySQL 客户端执行。

前端开发模式：

```bash
cd frontend
npm run dev
```

## API 概览

### 认证

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

`POST /auth/login` 使用 `application/x-www-form-urlencoded` 表单提交：

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=password123"
```

### 会话

- `GET /chat/sessions?mode=general|knowledge_base`
- `POST /chat/sessions`
- `GET /chat/sessions/{session_id}/messages`
- `POST /chat/sessions/{session_id}/stream`
- `DELETE /chat/sessions/{session_id}`

说明：

- 所有 `/chat/*` 接口都需要 `Authorization: Bearer <token>`
- 会话和消息都按登录用户隔离
- 普通问答支持多个会话
- 首条问题会自动触发标题生成

### 文档

- `POST /documents/upload`
- `GET /documents`

### 问答兼容接口

- `POST /qa/ask`
- `POST /qa/title`
- `POST /qa/ask/stream`

## LangSmith

启用 tracing 后，以下链路会进入 LangSmith：

- 文档解析与索引
- 普通问答
- 知识库问答
- 对话标题生成

## Tavily 联网搜索

普通问答现在会在有 `TAVILY_API_KEY` 时自动接入 Tavily 联网检索，把搜索结果作为上下文补充给模型。
如果你不填这个 key，系统会自动退回到纯模型回答，不影响知识库问答。

把下面配置改成 `true` 并填写你的 LangSmith API Key：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=knowledge-base-qa
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## 测试

运行：

```bash
pytest
```

覆盖范围：

- `/health`
- `/qa/ask` 接口契约
- 用户注册、登录、`/auth/me`
- 按用户隔离的会话和聊天记录

## 备注

- 项目启动时会自动创建 MySQL 表结构
- 如果你本地还没建库，先创建数据库，再启动后端
- 如果 MySQL 8 默认账号认证报 `cryptography` 相关错误，确认已安装 `cryptography`，或者把该账号的认证插件改成 `mysql_native_password`
- 前端页面已经按照普通问答、知识库问答和索引创建做了入口分离
