<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import { fetchDocuments, streamQuestion, uploadDocument } from "./api";

const documents = ref([]);
const selectedFile = ref(null);
const uploadMessage = ref("");
const uploadError = ref("");
const isUploading = ref(false);

const supportTypes = ".txt,.md,.pdf,.docx";

const tabs = [
  { key: "general", label: "普通问答", hint: "独立对话框" },
  { key: "knowledge_base", label: "知识库检索", hint: "基于已上传文档" },
];

const currentTab = ref("general");

const conversations = reactive({
  general: [],
  knowledge_base: [],
});

const inputs = reactive({
  general: "",
  knowledge_base: "",
});

const topK = reactive({
  general: 3,
  knowledge_base: 3,
});

const loading = reactive({
  general: false,
  knowledge_base: false,
});

const answerSource = reactive({
  general: "",
  knowledge_base: "",
});

const matches = reactive({
  general: [],
  knowledge_base: [],
});

const scrollAnchors = reactive({
  general: null,
  knowledge_base: null,
});

const documentCountText = computed(() => `已入库文档 ${documents.value.length} 份`);

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

function handleFileChange(event) {
  const [file] = event.target.files || [];
  selectedFile.value = file || null;
  uploadMessage.value = "";
  uploadError.value = "";
}

async function loadDocuments() {
  try {
    const result = await fetchDocuments();
    documents.value = result.documents;
  } catch (error) {
    uploadError.value = error.message;
  }
}

async function submitUpload() {
  if (!selectedFile.value) {
    uploadError.value = "请先选择一个知识文档。";
    return;
  }

  isUploading.value = true;
  uploadError.value = "";
  uploadMessage.value = "";

  try {
    const result = await uploadDocument(selectedFile.value);
    uploadMessage.value = `${result.filename} 上传成功，已切分 ${result.chunk_count} 个片段。`;
    selectedFile.value = null;
    const input = document.getElementById("file-input");
    if (input) {
      input.value = "";
    }
    await loadDocuments();
  } catch (error) {
    uploadError.value = error.message;
  } finally {
    isUploading.value = false;
  }
}

function pushUserMessage(mode, text) {
  conversations[mode].push({
    role: "user",
    content: text,
  });
}

function pushAssistantMessage(mode) {
  conversations[mode].push({
    role: "assistant",
    content: "",
    streaming: true,
  });
}

async function submitQuestion(mode) {
  const questionText = inputs[mode].trim();
  if (!questionText || loading[mode]) {
    return;
  }

  loading[mode] = true;
  answerSource[mode] = "";
  matches[mode] = [];

  pushUserMessage(mode, questionText);
  pushAssistantMessage(mode);
  scrollToBottom(mode);

  let bufferedText = "";

  try {
    await streamQuestion(
      {
        question: questionText,
        top_k: topK[mode],
        mode,
        stream: true,
      },
      (meta) => {
        answerSource[mode] = meta.answer_source;
        matches[mode] = meta.matches || [];
      },
      (token) => {
        bufferedText += token;
        const lastMessage = conversations[mode][conversations[mode].length - 1];
        if (lastMessage) {
          lastMessage.content = bufferedText;
        }
        scrollToBottom(mode);
      },
      () => {
        const lastMessage = conversations[mode][conversations[mode].length - 1];
        if (lastMessage) {
          lastMessage.streaming = false;
        }
      }
    );
    inputs[mode] = "";
  } catch (error) {
    conversations[mode].pop();
    conversations[mode].push({
      role: "assistant",
      content: error.message,
      streaming: false,
    });
  } finally {
    loading[mode] = false;
    scrollToBottom(mode);
  }
}

function switchTab(key) {
  currentTab.value = key;
}

onMounted(() => {
  loadDocuments();
});
</script>

<template>
  <div class="page-shell">
    <div class="page-background"></div>
    <main class="layout">
      <section class="hero-card">
        <div class="hero-top">
          <div>
            <p class="eyebrow">FastAPI + Vue 3</p>
            <h1>双入口问答工作台</h1>
            <p class="hero-copy">
              普通问答和知识库检索分开展示，回答以对话气泡形式逐步流式输出。
            </p>
          </div>
          <div class="hero-metrics">
            <div class="metric-card">
              <span class="metric-label">知识库状态</span>
              <strong>{{ documentCountText }}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">当前展示</span>
              <strong>{{ currentTab === 'general' ? '普通问答' : '知识库检索' }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="management-grid">
        <article class="panel upload-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Document</p>
              <h2>上传知识文档</h2>
            </div>
            <span class="badge">本地入库</span>
          </div>

          <label class="upload-dropzone" for="file-input">
            <input id="file-input" :accept="supportTypes" type="file" @change="handleFileChange" />
            <span class="dropzone-title">拖拽文件到这里，或点击选择</span>
            <span class="dropzone-subtitle">支持 txt、md、pdf、docx</span>
            <span v-if="selectedFile" class="selected-file">{{ selectedFile.name }}</span>
          </label>

          <button class="primary-button" :disabled="isUploading" @click="submitUpload">
            {{ isUploading ? "上传中..." : "上传并建立索引" }}
          </button>

          <p v-if="uploadMessage" class="status success">{{ uploadMessage }}</p>
          <p v-if="uploadError" class="status error">{{ uploadError }}</p>

          <div class="document-list">
            <div class="panel-header compact">
              <div>
                <p class="panel-kicker">Indexed</p>
                <h3>已上传文档</h3>
              </div>
            </div>
            <div v-if="documents.length" class="document-items">
              <div v-for="doc in documents" :key="doc.document_id" class="document-item">
                <div>
                  <strong>{{ doc.filename }}</strong>
                  <p>{{ doc.chunk_count }} 个片段</p>
                </div>
                <code>{{ doc.document_id.slice(0, 8) }}</code>
              </div>
            </div>
            <p v-else class="empty-text">还没有文档，先上传一个知识文件。</p>
          </div>
        </article>

        <article class="panel chat-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Chat</p>
              <h2>对话区</h2>
            </div>
            <div class="tab-strip">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                class="tab-button"
                :class="{ active: currentTab === tab.key }"
                @click="switchTab(tab.key)"
              >
                <span>{{ tab.label }}</span>
                <small>{{ tab.hint }}</small>
              </button>
            </div>
          </div>

          <div class="tab-panel" v-show="currentTab === 'general'">
            <div class="chat-shell">
              <div class="chat-header">
                <div>
                  <h3>普通问答</h3>
                  <p>不依赖知识库，适合一般性提问。</p>
                </div>
                <div class="chat-controls">
                  <label class="field-inline">
                    <span>流式输出</span>
                    <strong>开启</strong>
                  </label>
                </div>
              </div>

              <div class="chat-window" :ref="(el) => setScrollAnchor('general', el)">
                <div
                  v-for="(msg, index) in conversations.general"
                  :key="index"
                  class="bubble-row"
                  :class="msg.role"
                >
                  <div class="bubble" :class="{ streaming: msg.streaming }">
                    <p class="bubble-label">{{ msg.role === 'user' ? '我' : '助手' }}</p>
                    <p class="bubble-text">{{ msg.content }}</p>
                  </div>
                </div>
                <div v-if="!conversations.general.length" class="chat-empty">
                  在这里输入问题，答案会以对话气泡形式逐步流式输出。
                </div>
              </div>

              <div class="chat-footer">
                <textarea
                  v-model="inputs.general"
                  class="question-input compact"
                  placeholder="例如：FastAPI 和 Vue 3 分别适合做什么？"
                  rows="3"
                  @keydown.enter.exact.prevent="submitQuestion('general')"
                />
                <button class="primary-button" :disabled="loading.general" @click="submitQuestion('general')">
                  {{ loading.general ? '生成中...' : '发送' }}
                </button>
              </div>
            </div>
          </div>

          <div class="tab-panel" v-show="currentTab === 'knowledge_base'">
            <div class="chat-shell">
              <div class="chat-header">
                <div>
                  <h3>知识库检索</h3>
                  <p>先检索文档，再基于命中文内容生成答案。</p>
                </div>
                <div class="chat-controls">
                  <label class="field-inline">
                    <span>返回片段数</span>
                    <select v-model="topK.knowledge_base" class="select-input">
                      <option :value="1">1</option>
                      <option :value="2">2</option>
                      <option :value="3">3</option>
                      <option :value="4">4</option>
                      <option :value="5">5</option>
                    </select>
                  </label>
                </div>
              </div>

              <div class="chat-window" :ref="(el) => setScrollAnchor('knowledge_base', el)">
                <div
                  v-for="(msg, index) in conversations.knowledge_base"
                  :key="index"
                  class="bubble-row"
                  :class="msg.role"
                >
                  <div class="bubble" :class="{ streaming: msg.streaming, knowledge: msg.role === 'assistant' }">
                    <p class="bubble-label">{{ msg.role === 'user' ? '我' : '知识库助手' }}</p>
                    <p class="bubble-text">{{ msg.content }}</p>
                  </div>
                </div>
                <div v-if="!conversations.knowledge_base.length" class="chat-empty">
                  输入问题后会先检索文档，再逐步输出答案。
                </div>
              </div>

              <div class="match-panel" v-if="matches.knowledge_base.length">
                <div class="match-header">
                  <strong>命中文档片段</strong>
                  <code>{{ answerSource.knowledge_base }}</code>
                </div>
                <div class="match-items">
                  <div v-for="match in matches.knowledge_base" :key="match.chunk_id" class="match-item">
                    <div class="match-meta">
                      <strong>{{ match.filename }}</strong>
                      <code>{{ match.chunk_id }}</code>
                    </div>
                    <p>{{ match.content }}</p>
                  </div>
                </div>
              </div>

              <div class="chat-footer">
                <textarea
                  v-model="inputs.knowledge_base"
                  class="question-input compact"
                  placeholder="例如：这个项目支持哪些文件格式？"
                  rows="3"
                  @keydown.enter.exact.prevent="submitQuestion('knowledge_base')"
                />
                <button
                  class="primary-button"
                  :disabled="loading.knowledge_base"
                  @click="submitQuestion('knowledge_base')"
                >
                  {{ loading.knowledge_base ? '检索中...' : '发送' }}
                </button>
              </div>
            </div>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>
