<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { Delete, FolderAdd, Plus, RefreshRight, SwitchButton, UserFilled } from "@element-plus/icons-vue";

import TopNav from "./components/TopNav.vue";
import {
  createChatSession,
  deleteChatSession,
  fetchChatMessages,
  fetchChatSessions,
  fetchCurrentUser,
  fetchDocuments,
  loginUser,
  registerUser,
  streamQuestion,
  uploadDocument,
} from "./api";

const authToken = ref(localStorage.getItem("kb_token") || "");
const currentUser = ref(null);
const bootstrapping = ref(true);
const authMode = ref("login");
const authLoading = ref(false);
const authError = ref("");

const authForm = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

const activeSection = ref("general");
const documents = ref([]);
const uploadRef = ref();
const selectedFile = ref(null);
const uploadMessage = ref("");
const uploadError = ref("");
const isUploading = ref(false);

const sections = [
  { key: "general", label: "普通问答", desc: "多会话聊天" },
  { key: "knowledge_base", label: "知识库问答", desc: "检索增强生成" },
  { key: "index", label: "创建索引", desc: "上传文档入库" },
];

const generalState = reactive({
  sessions: [],
  activeId: null,
  draft: "",
  loading: false,
});

const knowledgeState = reactive({
  sessions: [],
  activeId: null,
  draft: "",
  loading: false,
  topK: 3,
  messages: [],
  matches: [],
  answerSource: "",
});

const scrollAnchors = reactive({
  general: null,
  knowledge_base: null,
});

const documentCountText = computed(() => `已入库文档 ${documents.value.length} 份`);
const activeSectionLabel = computed(() => sections.find((item) => item.key === activeSection.value)?.label || "普通问答");

const activeGeneralSession = computed(
  () => generalState.sessions.find((session) => session.id === generalState.activeId) || null
);
const activeKnowledgeSession = computed(
  () => knowledgeState.sessions.find((session) => session.id === knowledgeState.activeId) || null
);

const generalDraft = computed({
  get() {
    return activeGeneralSession.value?.draft || "";
  },
  set(value) {
    if (activeGeneralSession.value) {
      activeGeneralSession.value.draft = value;
    }
  },
});

const knowledgeDraft = computed({
  get() {
    return activeKnowledgeSession.value?.draft || "";
  },
  set(value) {
    if (activeKnowledgeSession.value) {
      activeKnowledgeSession.value.draft = value;
    }
  },
});

function createLocalSession(session) {
  return {
    ...session,
    draft: session.draft || "",
    messages: session.messages || [],
  };
}

function setScrollAnchor(key, el) {
  scrollAnchors[key] = el;
}

function scrollToBottom(key) {
  requestAnimationFrame(() => {
    const el = scrollAnchors[key];
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  });
}

function switchSection(key) {
  activeSection.value = key;
}

function handleFileChange(uploadFile) {
  selectedFile.value = uploadFile?.raw || null;
  uploadMessage.value = "";
  uploadError.value = "";
}

async function loadDocuments() {
  const result = await fetchDocuments();
  documents.value = result.documents;
}

async function loadChatSessions(mode, autoCreate = true) {
  const remote = await fetchChatSessions(mode, authToken.value);
  const target = mode === "general" ? generalState : knowledgeState;
  const localById = new Map(target.sessions.map((session) => [session.id, session]));

  target.sessions = remote.map((session) => {
    const existing = localById.get(session.id);
    return createLocalSession({
      ...session,
      draft: existing?.draft || "",
      messages: existing?.messages || [],
    });
  });

  if (!target.sessions.length && autoCreate) {
    const created = await createChatSession(mode, authToken.value);
    target.sessions = [createLocalSession({ ...created, draft: "", messages: [] })];
  }

  if (!target.activeId || !target.sessions.some((session) => session.id === target.activeId)) {
    target.activeId = target.sessions[0]?.id || null;
  }
}

async function loadSessionMessages(mode, sessionId) {
  const target = mode === "general" ? generalState : knowledgeState;
  if (!sessionId) {
    target.messages = [];
    return;
  }

  const remote = await fetchChatMessages(sessionId, authToken.value);
  const session = target.sessions.find((item) => item.id === sessionId);
  if (session) {
    session.messages = remote;
  }
  if (mode === "knowledge_base") {
    knowledgeState.messages = remote;
  }
}

async function refreshWorkspace() {
  await Promise.all([
    loadDocuments(),
    loadChatSessions("general"),
    loadChatSessions("knowledge_base"),
  ]);
  await Promise.all([
    loadSessionMessages("general", generalState.activeId),
    loadSessionMessages("knowledge_base", knowledgeState.activeId),
  ]);
}

async function bootstrapAuth() {
  if (!authToken.value) {
    bootstrapping.value = false;
    return;
  }

  try {
    const result = await fetchCurrentUser(authToken.value);
    currentUser.value = result.user;
    await refreshWorkspace();
  } catch {
    logout();
  } finally {
    bootstrapping.value = false;
  }
}

async function submitAuth() {
  authLoading.value = true;
  authError.value = "";
  try {
    if (authMode.value === "register") {
      if (authForm.password !== authForm.confirmPassword) {
        throw new Error("两次输入的密码不一致。");
      }
      await registerUser({
        username: authForm.username,
        password: authForm.password,
      });
    }

    const login = await loginUser(authForm.username, authForm.password);
    authToken.value = login.access_token;
    localStorage.setItem("kb_token", login.access_token);

    const result = await fetchCurrentUser(authToken.value);
    currentUser.value = result.user;
    await refreshWorkspace();
  } catch (error) {
    authError.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

function logout() {
  authToken.value = "";
  currentUser.value = null;
  localStorage.removeItem("kb_token");
  generalState.sessions = [];
  generalState.activeId = null;
  generalState.draft = "";
  generalState.loading = false;
  knowledgeState.sessions = [];
  knowledgeState.activeId = null;
  knowledgeState.draft = "";
  knowledgeState.loading = false;
  knowledgeState.messages = [];
  knowledgeState.matches = [];
  knowledgeState.answerSource = "";
}

function ensureActiveSession(mode) {
  const target = mode === "general" ? generalState : knowledgeState;
  if (target.activeId) {
    return target.sessions.find((session) => session.id === target.activeId) || null;
  }
  return null;
}

async function createNewSession(mode) {
  const created = await createChatSession(mode, authToken.value);
  const target = mode === "general" ? generalState : knowledgeState;
  target.sessions.unshift(createLocalSession({ ...created, draft: "", messages: [] }));
  target.activeId = created.id;
  target.draft = "";
  if (mode === "knowledge_base") {
    knowledgeState.messages = [];
    knowledgeState.matches = [];
    knowledgeState.answerSource = "";
  }
  return target.sessions[0];
}

async function selectSession(mode, sessionId) {
  const target = mode === "general" ? generalState : knowledgeState;
  target.activeId = sessionId;
  await loadSessionMessages(mode, sessionId);
  scrollToBottom(mode);
}

async function removeSession(mode, sessionId) {
  await deleteChatSession(sessionId, authToken.value);
  const target = mode === "general" ? generalState : knowledgeState;
  target.sessions = target.sessions.filter((session) => session.id !== sessionId);
  if (target.activeId === sessionId) {
    target.activeId = target.sessions[0]?.id || null;
    await loadSessionMessages(mode, target.activeId);
  }
}

function pushUserMessage(mode, text) {
  const target = mode === "general" ? generalState : knowledgeState;
  const session = ensureActiveSession(mode);
  session?.messages.push({ role: "user", content: text });
  if (mode === "knowledge_base") {
    target.messages = session?.messages || [];
  }
}

function pushAssistantMessage(mode) {
  const target = mode === "general" ? generalState : knowledgeState;
  const session = ensureActiveSession(mode);
  const message = {
    role: "assistant",
    content: "",
    streaming: true,
    streamBuffer: "",
    streamTimer: null,
  };
  session?.messages.push(message);
  if (mode === "knowledge_base") {
    target.messages = session?.messages || [];
  }
  return message;
}

function startStreamDrain(message, mode) {
  if (message.streamTimer) {
    return;
  }

  message.streamTimer = window.setInterval(() => {
    if (!message.streamBuffer?.length) {
      if (!message.streaming) {
        window.clearInterval(message.streamTimer);
        message.streamTimer = null;
      }
      return;
    }

    const step = message.streamBuffer.slice(0, 6);
    message.streamBuffer = message.streamBuffer.slice(6);
    message.content += step;
    scrollToBottom(mode);

    if (!message.streaming && !message.streamBuffer.length) {
      window.clearInterval(message.streamTimer);
      message.streamTimer = null;
    }
  }, 16);
}

function queueStreamChunk(message, chunk, mode) {
  if (!chunk) {
    return;
  }

  message.streamBuffer = `${message.streamBuffer || ""}${chunk}`;
  startStreamDrain(message, mode);
}

function finishStreamMessage(message, mode) {
  message.streaming = false;
  startStreamDrain(message, mode);
}

function waitForStreamDrain(message) {
  return new Promise((resolve) => {
    const poll = () => {
      if (!message.streaming && !message.streamBuffer?.length && !message.streamTimer) {
        resolve();
        return;
      }
      window.setTimeout(poll, 30);
    };
    poll();
  });
}

async function submitGeneralQuestion() {
  const session = ensureActiveSession("general") || (await createNewSession("general"));
  const questionText = session.draft.trim();
  if (!questionText || generalState.loading) {
    return;
  }

  generalState.loading = true;
  session.draft = "";
  pushUserMessage("general", questionText);
  const assistantMessage = pushAssistantMessage("general");
  scrollToBottom("general");

  try {
    await streamQuestion(
      session.id,
      {
        question: questionText,
        top_k: 3,
        mode: "general",
        stream: true,
      },
      authToken.value,
      () => {},
      (token) => {
        queueStreamChunk(assistantMessage, token, "general");
        scrollToBottom("general");
      },
      () => {
        finishStreamMessage(assistantMessage, "general");
      }
    );
    await waitForStreamDrain(assistantMessage);
    await loadChatSessions("general", false);
    await loadSessionMessages("general", session.id);
  } catch (error) {
    assistantMessage.streaming = false;
    assistantMessage.streamBuffer = "";
    if (assistantMessage.streamTimer) {
      window.clearInterval(assistantMessage.streamTimer);
      assistantMessage.streamTimer = null;
    }
    session.messages.pop();
    session.messages.push({
      role: "assistant",
      content: error.message,
      streaming: false,
    });
  } finally {
    generalState.loading = false;
    scrollToBottom("general");
  }
}

async function submitKnowledgeQuestion() {
  const session = ensureActiveSession("knowledge_base") || (await createNewSession("knowledge_base"));
  const questionText = session.draft.trim();
  if (!questionText || knowledgeState.loading) {
    return;
  }

  knowledgeState.loading = true;
  session.draft = "";
  pushUserMessage("knowledge_base", questionText);
  const assistantMessage = pushAssistantMessage("knowledge_base");
  scrollToBottom("knowledge_base");

  try {
    await streamQuestion(
      session.id,
      {
        question: questionText,
        top_k: knowledgeState.topK,
        mode: "knowledge_base",
        stream: true,
      },
      authToken.value,
      (meta) => {
        knowledgeState.matches = meta.matches || [];
        knowledgeState.answerSource = meta.answer_source;
      },
      (token) => {
        queueStreamChunk(assistantMessage, token, "knowledge_base");
        scrollToBottom("knowledge_base");
      },
      () => {
        finishStreamMessage(assistantMessage, "knowledge_base");
      }
    );
    await waitForStreamDrain(assistantMessage);
    await loadChatSessions("knowledge_base", false);
    await loadSessionMessages("knowledge_base", session.id);
  } catch (error) {
    assistantMessage.streaming = false;
    assistantMessage.streamBuffer = "";
    if (assistantMessage.streamTimer) {
      window.clearInterval(assistantMessage.streamTimer);
      assistantMessage.streamTimer = null;
    }
    session.messages.pop();
    session.messages.push({
      role: "assistant",
      content: error.message,
      streaming: false,
    });
  } finally {
    knowledgeState.loading = false;
    scrollToBottom("knowledge_base");
  }
}

async function submitUpload() {
  if (!selectedFile.value) {
    uploadError.value = "请先选择一个知识文档。";
    return;
  }

  isUploading.value = true;
  uploadMessage.value = "";
  uploadError.value = "";
  try {
    const result = await uploadDocument(selectedFile.value);
    uploadMessage.value = `${result.filename} 上传成功，已切分 ${result.chunk_count} 个片段。`;
    selectedFile.value = null;
    uploadRef.value?.clearFiles?.();
    await loadDocuments();
  } catch (error) {
    uploadError.value = error.message;
  } finally {
    isUploading.value = false;
  }
}

function sessionTitle(session) {
  return session?.title || "新对话";
}

function sessionPreview(session) {
  const userMessage = [...(session?.messages || [])].reverse().find((message) => message.role === "user");
  return userMessage?.content || "等待第一条消息";
}

onMounted(bootstrapAuth);
</script>

<template>
  <div v-if="bootstrapping" class="bootstrap-screen">
    <el-skeleton animated :rows="6" />
  </div>

  <div v-else-if="!currentUser" class="auth-shell">
    <div class="auth-glow auth-glow-left"></div>
    <div class="auth-glow auth-glow-right"></div>

    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="auth-header">
          <div>
            <div class="brand-badge">KB Studio</div>
            <h1>欢迎使用知识库问答</h1>
            <p>登录后会话和聊天记录将按用户保存到 MySQL。</p>
          </div>
        </div>
      </template>

      <el-form label-position="top" class="auth-form">
        <el-form-item label="用户名">
          <el-input v-model="authForm.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input v-model="authForm.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>

        <el-form-item v-if="authMode === 'register'" label="确认密码">
          <el-input v-model="authForm.confirmPassword" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>

        <el-alert v-if="authError" :closable="false" type="error" :title="authError" show-icon />

        <div class="auth-actions">
          <el-button type="primary" size="large" :loading="authLoading" @click="submitAuth">
            {{ authMode === 'login' ? '登录' : '注册并登录' }}
          </el-button>
          <el-button text @click="authMode = authMode === 'login' ? 'register' : 'login'">
            {{ authMode === 'login' ? '没有账号，去注册' : '已有账号，去登录' }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>

  <div v-else class="page-shell">
    <div class="page-glow page-glow-left"></div>
    <div class="page-glow page-glow-right"></div>

    <el-container class="app-shell">
      <el-aside width="292px" class="app-aside">
        <TopNav :sections="sections" :active-key="activeSection" @change="switchSection" />
      </el-aside>

      <el-container class="app-content">
        <el-header class="workspace-header">
          <div class="workspace-title">
            <el-tag type="success" effect="light" round>FastAPI + Vue 3 + Element Plus</el-tag>
            <h2>{{ activeSectionLabel }}</h2>
            <p>
              普通问答支持多会话和自动标题生成。登录状态、会话和聊天记录都由 MySQL 持久化保存。
            </p>
          </div>
          <div class="workspace-stats">
            <el-card shadow="never" class="stat-card">
              <span>当前用户</span>
              <strong>{{ currentUser.username }}</strong>
            </el-card>
            <el-card shadow="never" class="stat-card accent">
              <span>知识库状态</span>
              <strong>{{ documentCountText }}</strong>
            </el-card>
          </div>
          <div class="workspace-user">
            <el-button text :icon="RefreshRight" @click="refreshWorkspace">刷新</el-button>
            <el-button text :icon="SwitchButton" @click="logout">退出登录</el-button>
          </div>
        </el-header>

        <el-main class="workspace-main">
          <section v-show="activeSection === 'general'" class="section-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :lg="7">
                <el-card class="panel-card session-panel" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">普通问答</p>
                        <h3>会话列表</h3>
                      </div>
                      <el-button type="primary" plain :icon="Plus" @click="createNewSession('general')">
                        新建
                      </el-button>
                    </div>
                  </template>

                  <div class="session-list">
                    <button
                      v-for="session in generalState.sessions"
                      :key="session.id"
                      class="session-item"
                      :class="{ active: session.id === generalState.activeId }"
                      @click="selectSession('general', session.id)"
                    >
                      <div class="session-main">
                        <strong>{{ sessionTitle(session) }}</strong>
                        <p>{{ sessionPreview(session) }}</p>
                      </div>
                      <div class="session-meta">
                        <el-tag v-if="session.title_generated" type="success" size="small">已命名</el-tag>
                        <el-button
                          text
                          circle
                          class="remove-button"
                          :icon="Delete"
                          @click.stop="removeSession('general', session.id)"
                        />
                      </div>
                    </button>
                  </div>
                </el-card>
              </el-col>

              <el-col :xs="24" :lg="17">
                <el-card class="panel-card chat-card" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">会话中</p>
                        <h3>{{ sessionTitle(activeGeneralSession) }}</h3>
                      </div>
                      <el-tag type="info" effect="plain">流式输出</el-tag>
                    </div>
                  </template>

                  <div class="chat-shell">
                    <div class="chat-topline">
                      <div>
                        <h4>普通问答</h4>
                        <p>不依赖知识库，适合一般性提问。</p>
                      </div>
                      <el-tag type="success" effect="light">多轮会话</el-tag>
                    </div>

                    <div :ref="(el) => setScrollAnchor('general', el)" class="chat-window">
                      <div
                        v-for="(message, index) in activeGeneralSession?.messages || []"
                        :key="index"
                        class="bubble-row"
                        :class="message.role"
                      >
                        <div class="bubble" :class="{ streaming: message.streaming }">
                          <div class="bubble-meta">
                            <span>{{ message.role === 'user' ? '我' : '助手' }}</span>
                          </div>
                          <div class="bubble-text">
                            <span>{{ message.content }}</span>
                            <span v-if="message.streaming" class="typing-cursor">▍</span>
                          </div>
                        </div>
                      </div>

                      <el-empty
                        v-if="!(activeGeneralSession?.messages?.length)"
                        description="新建一个对话，然后输入第一个问题，标题会自动生成。"
                      />
                    </div>

                    <div class="chat-footer">
                      <el-input
                        v-model="generalDraft"
                        type="textarea"
                        :rows="4"
                        resize="none"
                        placeholder="例如：FastAPI 和 Vue 3 分别适合做什么？"
                        @keydown.enter.exact.prevent="submitGeneralQuestion"
                      />
                      <div class="action-row">
                        <span class="hint">回车发送，Shift+Enter 换行</span>
                        <el-button type="primary" :loading="generalState.loading" @click="submitGeneralQuestion">
                          发送
                        </el-button>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </section>

          <section v-show="activeSection === 'knowledge_base'" class="section-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :lg="7">
                <el-card class="panel-card session-panel" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">知识库问答</p>
                        <h3>会话列表</h3>
                      </div>
                      <el-button type="warning" plain :icon="Plus" @click="createNewSession('knowledge_base')">
                        新建
                      </el-button>
                    </div>
                  </template>

                  <div class="session-list">
                    <button
                      v-for="session in knowledgeState.sessions"
                      :key="session.id"
                      class="session-item"
                      :class="{ active: session.id === knowledgeState.activeId }"
                      @click="selectSession('knowledge_base', session.id)"
                    >
                      <div class="session-main">
                        <strong>{{ sessionTitle(session) }}</strong>
                        <p>{{ sessionPreview(session) }}</p>
                      </div>
                      <div class="session-meta">
                        <el-tag v-if="session.title_generated" type="success" size="small">已命名</el-tag>
                        <el-button
                          text
                          circle
                          class="remove-button"
                          :icon="Delete"
                          @click.stop="removeSession('knowledge_base', session.id)"
                        />
                      </div>
                    </button>
                  </div>
                </el-card>
              </el-col>

              <el-col :xs="24" :lg="10">
                <el-card class="panel-card chat-card" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">会话中</p>
                        <h3>{{ sessionTitle(activeKnowledgeSession) }}</h3>
                      </div>
                      <el-tag type="warning" effect="plain">检索增强</el-tag>
                    </div>
                  </template>

                  <div class="chat-shell">
                    <div class="chat-topline">
                      <div>
                        <h4>知识库助手</h4>
                        <p>先检索文档，再基于命中内容生成答案。</p>
                      </div>
                      <el-select v-model="knowledgeState.topK" class="topk-select" size="small">
                        <el-option :value="1" label="1 个片段" />
                        <el-option :value="2" label="2 个片段" />
                        <el-option :value="3" label="3 个片段" />
                        <el-option :value="4" label="4 个片段" />
                        <el-option :value="5" label="5 个片段" />
                      </el-select>
                    </div>

                    <div :ref="(el) => setScrollAnchor('knowledge_base', el)" class="chat-window">
                      <div
                        v-for="(message, index) in knowledgeState.messages"
                        :key="index"
                        class="bubble-row"
                        :class="message.role"
                      >
                        <div class="bubble" :class="{ streaming: message.streaming, knowledge: message.role === 'assistant' }">
                          <div class="bubble-meta">
                            <span>{{ message.role === 'user' ? '我' : '知识库助手' }}</span>
                          </div>
                          <div class="bubble-text">
                            <span>{{ message.content }}</span>
                            <span v-if="message.streaming" class="typing-cursor">▍</span>
                          </div>
                        </div>
                      </div>

                      <el-empty
                        v-if="!knowledgeState.messages.length"
                        description="选择一个会话或新建一个会话，然后开始检索问答。"
                      />
                    </div>

                    <div v-if="knowledgeState.matches.length" class="match-panel">
                      <div class="match-header">
                        <strong>命中文档片段</strong>
                        <el-tag type="success" effect="plain">{{ knowledgeState.answerSource }}</el-tag>
                      </div>

                      <div class="match-list">
                        <div v-for="match in knowledgeState.matches" :key="match.chunk_id" class="match-item">
                          <div class="match-top">
                            <strong>{{ match.filename }}</strong>
                            <code>{{ match.chunk_id }}</code>
                          </div>
                          <p>{{ match.content }}</p>
                        </div>
                      </div>
                    </div>

                    <div class="chat-footer">
                      <el-input
                        v-model="knowledgeDraft"
                        type="textarea"
                        :rows="4"
                        resize="none"
                        placeholder="例如：这个项目支持哪些文件格式？"
                        @keydown.enter.exact.prevent="submitKnowledgeQuestion"
                      />
                      <div class="action-row">
                        <span class="hint">回车发送，Shift+Enter 换行</span>
                        <el-button type="warning" :loading="knowledgeState.loading" @click="submitKnowledgeQuestion">
                          发送
                        </el-button>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-col>

              <el-col :xs="24" :lg="7">
                <el-card class="panel-card info-card" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">知识库</p>
                        <h3>当前索引状态</h3>
                      </div>
                      <el-tag type="info" effect="plain">{{ documents.length }} 份文档</el-tag>
                    </div>
                  </template>

                  <el-empty
                    v-if="!documents.length"
                    description="先去创建索引入口上传知识文档，再回来提问。"
                  />

                  <div v-else class="kb-doc-list">
                    <div v-for="doc in documents" :key="doc.document_id" class="kb-doc-card">
                      <strong>{{ doc.filename }}</strong>
                      <p>{{ doc.chunk_count }} 个片段 · {{ doc.document_id.slice(0, 8) }}</p>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </section>

          <section v-show="activeSection === 'index'" class="section-grid">
            <el-row :gutter="20">
              <el-col :xs="24" :lg="10">
                <el-card class="panel-card index-card" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">创建索引</p>
                        <h3>上传知识文档</h3>
                      </div>
                      <el-tag type="success" effect="light">上传即入库</el-tag>
                    </div>
                  </template>

                  <el-upload
                    ref="uploadRef"
                    drag
                    :limit="1"
                    :auto-upload="false"
                    :show-file-list="false"
                    :accept="supportTypes"
                    class="upload-box"
                    @change="handleFileChange"
                  >
                    <el-icon class="upload-icon"><FolderAdd /></el-icon>
                    <div class="upload-title">点击选择或拖拽知识文档</div>
                    <div class="upload-desc">支持 txt、md、pdf、docx</div>
                    <div v-if="selectedFile" class="upload-file">已选择：{{ selectedFile.name }}</div>
                  </el-upload>

                  <div class="upload-actions">
                    <el-button type="success" size="large" :loading="isUploading" @click="submitUpload">
                      上传并建立索引
                    </el-button>
                  </div>

                  <el-alert
                    v-if="uploadMessage"
                    type="success"
                    :closable="false"
                    show-icon
                    :title="uploadMessage"
                  />
                  <el-alert
                    v-if="uploadError"
                    type="error"
                    :closable="false"
                    show-icon
                    :title="uploadError"
                  />
                </el-card>
              </el-col>

              <el-col :xs="24" :lg="14">
                <el-card class="panel-card" shadow="hover">
                  <template #header>
                    <div class="panel-header">
                      <div>
                        <p class="eyebrow">已入库</p>
                        <h3>文档索引列表</h3>
                      </div>
                      <el-tag type="info" effect="plain">{{ documents.length }} 份文档</el-tag>
                    </div>
                  </template>

                  <el-table :data="documents" stripe border class="docs-table" height="560">
                    <el-table-column prop="filename" label="文件名" min-width="180" />
                    <el-table-column prop="chunk_count" label="片段数" width="100" align="center" />
                    <el-table-column prop="document_id" label="文档 ID" min-width="220" />
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </section>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>
