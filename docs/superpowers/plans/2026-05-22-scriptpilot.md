# ScriptPilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI Agent that takes a topic, runs a 4-stage LangGraph pipeline (research → outline → content → script), and streams results via SSE to a Vue 3 frontend.

**Architecture:** FastAPI backend serves SSE events from a LangGraph pipeline. Each node calls DeepSeek via ChatOpenAI. Vue 3 (Vite) frontend displays real-time streaming results in a tabbed interface. No database — MVP is stateless.

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, LangChain, DeepSeek API (via langchain-openai), Vue 3, Vite, Tailwind CSS (CDN), SSE

---

## File Map

| File | Responsibility |
|------|---------------|
| `backend/requirements.txt` | Python dependencies |
| `backend/.env` | DEEPSEEK_API_KEY (gitignored) |
| `.env.example` | Env var template |
| `backend/graph/state.py` | PipelineState TypedDict |
| `backend/prompts/research.py` | Research prompt template |
| `backend/prompts/outline.py` | Outline prompt template |
| `backend/prompts/content.py` | Content prompt template |
| `backend/prompts/script.py` | Script prompt template |
| `backend/nodes/research.py` | Research node + stream function |
| `backend/nodes/outline.py` | Outline node + stream function |
| `backend/nodes/content.py` | Content node + stream function |
| `backend/nodes/script.py` | Script node + stream function |
| `backend/graph/pipeline.py` | LangGraph graph builder + streaming orchestrator |
| `backend/app.py` | FastAPI app with SSE endpoint |
| `frontend/` | Vue 3 + Vite project (scaffolded) |
| `frontend/src/api/sse.js` | SSE client using fetch+ReadableStream |
| `frontend/src/components/TopicInput.vue` | Topic input + generate button |
| `frontend/src/components/ContentPanel.vue` | 4-tab streaming content display |
| `frontend/src/App.vue` | Main layout composing TopicInput + ContentPanel |

---

## Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `.env.example`
- Create: `backend/.env` (gitignored)
- Create: `backend/graph/__init__.py`
- Create: `backend/nodes/__init__.py`
- Create: `backend/prompts/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
mkdir -p backend/graph backend/nodes backend/prompts
touch backend/graph/__init__.py backend/nodes/__init__.py backend/prompts/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
langchain-openai==0.3.9
langchain-core==0.3.38
langgraph==0.4.1
python-dotenv==1.0.1
sse-starlette==2.2.1
```

- [ ] **Step 3: Write .env.example and .env**

`.env.example`:
```text
DEEPSEEK_API_KEY=your_api_key_here
```

`backend/.env`:
```text
DEEPSEEK_API_KEY=
```

- [ ] **Step 4: Write .gitignore**

```text
__pycache__/
*.pyc
.env
node_modules/
dist/
*.egg-info/
.venv/
backend/static/
```

- [ ] **Step 5: Initialize git and commit**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
git init
git add .
git commit -m "chore: project scaffolding with directory structure and dependencies"
```

---

## Task 2: State Definition and Prompt Templates

**Files:**
- Create: `backend/graph/state.py`
- Create: `backend/prompts/research.py`
- Create: `backend/prompts/outline.py`
- Create: `backend/prompts/content.py`
- Create: `backend/prompts/script.py`

- [ ] **Step 1: Define PipelineState**

`backend/graph/state.py`:
```python
from typing import TypedDict


class PipelineState(TypedDict):
    topic: str
    research: str
    outline: str
    content: str
    script: str
    current_stage: str
```

- [ ] **Step 2: Write research prompt**

`backend/prompts/research.py`:
```python
from langchain_core.prompts import ChatPromptTemplate

research_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位资深内容研究员。你的任务是针对给定主题，全面收集和整理相关资料。

请从以下维度进行资料收集：
1. 核心概念和定义
2. 历史背景和发展脉络
3. 关键数据和统计信息
4. 主要观点和不同立场
5. 最新发展趋势
6. 典型案例和实例

输出要求：
- 内容详实、有据可依
- 结构清晰，按维度分点整理
- 每个要点附带简要说明"""),
    ("human", "请针对以下主题进行全面深入的资料收集和整理：\n\n{topic}"),
])
```

- [ ] **Step 3: Write outline prompt**

`backend/prompts/outline.py`:
```python
from langchain_core.prompts import ChatPromptTemplate

outline_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的内容策划师。你的任务是基于研究资料，生成一个结构清晰、逻辑严谨的文章大纲。

大纲要求：
- 包含 3-5 个主要章节
- 每个章节包含 2-4 个子要点
- 章节之间有清晰的逻辑递进关系
- 从引入到深入再到总结
- 每个子要点用一句话概括核心内容

输出格式：
# 文章标题
## 一、章节标题
- 子要点1：简述
- 子要点2：简述"""),
    ("human", "基于以下研究资料，请生成一个结构清晰的文章大纲：\n\n{research}"),
])
```

- [ ] **Step 4: Write content prompt**

`backend/prompts/content.py`:
```python
from langchain_core.prompts import ChatPromptTemplate

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位优秀的专栏作家。你的任务是基于大纲和研究资料，撰写一篇高质量的文章。

写作要求：
- 语言流畅自然，论述充分
- 每个章节展开充分，有理有据
- 适当引用研究资料中的数据和案例
- 段落之间过渡自然
- 文章总字数控制在 1500-3000 字"""),
    ("human", "请基于以下大纲和研究资料撰写完整文章：\n\n## 大纲\n{outline}\n\n## 研究资料\n{research}"),
])
```

- [ ] **Step 5: Write script prompt**

`backend/prompts/script.py`:
```python
from langchain_core.prompts import ChatPromptTemplate

script_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的口播稿撰写人。你的任务是将文章内容改写为适合口头播报的稿子。

口播稿要求：
- 使用口语化表达，自然亲切
- 句子简短有力，节奏感强
- 加入自然的过渡语和衔接词
- 适当加入互动性表达（如"你知道吗"、"有意思的是"）
- 标注情感和语气提示（如[兴奋]、[低沉]）
- 每段开头有吸引人的引入语
- 结尾有号召性总结"""),
    ("human", "请将以下文章内容改写为口播稿：\n\n{content}"),
])
```

- [ ] **Step 6: Commit**

```bash
git add backend/graph/state.py backend/prompts/
git commit -m "feat: add PipelineState and prompt templates for all 4 stages"
```

---

## Task 3: LLM Config and Node Implementations

**Files:**
- Create: `backend/nodes/research.py`
- Create: `backend/nodes/outline.py`
- Create: `backend/nodes/content.py`
- Create: `backend/nodes/script.py`

- [ ] **Step 1: Write research node**

`backend/nodes/research.py`:
```python
import os
from langchain_openai import ChatOpenAI
from backend.graph.state import PipelineState
from backend.prompts.research import research_prompt

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    streaming=True,
)


def research_node(state: PipelineState) -> dict:
    chain = research_prompt | llm
    response = chain.invoke({"topic": state["topic"]})
    return {"research": response.content, "current_stage": "research"}


async def stream_research(state: PipelineState):
    chain = research_prompt | llm
    async for chunk in chain.astream({"topic": state["topic"]}):
        if chunk.content:
            yield chunk.content
```

- [ ] **Step 2: Write outline node**

`backend/nodes/outline.py`:
```python
from backend.graph.state import PipelineState
from backend.nodes.research import llm
from backend.prompts.outline import outline_prompt


def outline_node(state: PipelineState) -> dict:
    chain = outline_prompt | llm
    response = chain.invoke({"research": state["research"]})
    return {"outline": response.content, "current_stage": "outline"}


async def stream_outline(state: PipelineState):
    chain = outline_prompt | llm
    async for chunk in chain.astream({"research": state["research"]}):
        if chunk.content:
            yield chunk.content
```

- [ ] **Step 3: Write content node**

`backend/nodes/content.py`:
```python
from backend.graph.state import PipelineState
from backend.nodes.research import llm
from backend.prompts.content import content_prompt


def content_node(state: PipelineState) -> dict:
    chain = content_prompt | llm
    response = chain.invoke({
        "outline": state["outline"],
        "research": state["research"],
    })
    return {"content": response.content, "current_stage": "content"}


async def stream_content(state: PipelineState):
    chain = content_prompt | llm
    async for chunk in chain.astream({
        "outline": state["outline"],
        "research": state["research"],
    }):
        if chunk.content:
            yield chunk.content
```

- [ ] **Step 4: Write script node**

`backend/nodes/script.py`:
```python
from backend.graph.state import PipelineState
from backend.nodes.research import llm
from backend.prompts.script import script_prompt


def script_node(state: PipelineState) -> dict:
    chain = script_prompt | llm
    response = chain.invoke({"content": state["content"]})
    return {"script": response.content, "current_stage": "script"}


async def stream_script(state: PipelineState):
    chain = script_prompt | llm
    async for chunk in chain.astream({"content": state["content"]}):
        if chunk.content:
            yield chunk.content
```

- [ ] **Step 5: Commit**

```bash
git add backend/nodes/
git commit -m "feat: add LangGraph node functions and streaming functions for all 4 stages"
```

---

## Task 4: LangGraph Pipeline Builder

**Files:**
- Create: `backend/graph/pipeline.py`

- [ ] **Step 1: Write pipeline builder with streaming orchestrator**

`backend/graph/pipeline.py`:
```python
import json
from typing import AsyncGenerator

from langgraph.graph import StateGraph, START, END

from backend.graph.state import PipelineState
from backend.nodes.research import research_node, stream_research
from backend.nodes.outline import outline_node, stream_outline
from backend.nodes.content import content_node, stream_content
from backend.nodes.script import script_node, stream_script

STAGES = ["research", "outline", "content", "script"]

STREAM_FNS = {
    "research": stream_research,
    "outline": stream_outline,
    "content": stream_content,
    "script": stream_script,
}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("research", research_node)
    graph.add_node("outline", outline_node)
    graph.add_node("content", content_node)
    graph.add_node("script", script_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", "outline")
    graph.add_edge("outline", "content")
    graph.add_edge("content", "script")
    graph.add_edge("script", END)
    return graph.compile()


async def run_pipeline_streaming(topic: str) -> AsyncGenerator[str, None]:
    state: dict = {
        "topic": topic,
        "research": "",
        "outline": "",
        "content": "",
        "script": "",
        "current_stage": "",
    }

    for stage_name in STAGES:
        yield f"event: stage\ndata: {json.dumps({'stage': stage_name, 'status': 'running'})}\n\n"

        full_text = ""
        async for token in STREAM_FNS[stage_name](state):
            full_text += token
            yield f"event: token\ndata: {json.dumps({'stage': stage_name, 'token': token})}\n\n"

        state[stage_name] = full_text

        yield f"event: stage\ndata: {json.dumps({'stage': stage_name, 'status': 'completed'})}\n\n"

    yield f"event: done\ndata: {json.dumps(state)}\n\n"
```

- [ ] **Step 2: Commit**

```bash
git add backend/graph/pipeline.py
git commit -m "feat: add LangGraph pipeline builder with streaming orchestrator"
```

---

## Task 5: FastAPI App with SSE Endpoint

**Files:**
- Create: `backend/app.py`

- [ ] **Step 1: Write FastAPI application**

`backend/app.py`:
```python
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from backend.graph.pipeline import run_pipeline_streaming

load_dotenv()

app = FastAPI(title="ScriptPilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        async for event in run_pipeline_streaming(topic):
            yield event

    return EventSourceResponse(event_generator())


# Serve Vue build output in production
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
```

- [ ] **Step 2: Verify backend starts**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
pip install -r backend/requirements.txt
DEEPSEEK_API_KEY=test uvicorn backend.app:app --reload
```

Expected: Server starts without errors, `GET /api/health` returns `{"status": "ok"}`

- [ ] **Step 3: Commit**

```bash
git add backend/app.py
git commit -m "feat: add FastAPI app with SSE endpoint and health check"
```

---

## Task 6: Frontend Scaffolding (Vue 3 + Vite)

**Files:**
- Create: `frontend/` (via `npm create vue@latest`)
- Modify: `frontend/index.html` (add Tailwind CDN)
- Modify: `frontend/vite.config.js` (add API proxy)

- [ ] **Step 1: Scaffold Vue 3 project**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
npm create vue@latest frontend -- --default
cd frontend && npm install
```

- [ ] **Step 2: Add Tailwind CSS via CDN in index.html**

Replace `frontend/index.html` with:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScriptPilot - AI 口播稿生成器</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-gray-50 min-h-screen">
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 3: Configure Vite proxy for API**

Replace `frontend/vite.config.js` with:

```javascript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

- [ ] **Step 4: Verify frontend starts**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot/frontend
npm run dev
```

Expected: Vite dev server starts, page loads at `http://localhost:5173`

- [ ] **Step 5: Commit**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
git add frontend/
git commit -m "feat: scaffold Vue 3 + Vite frontend with Tailwind and API proxy"
```

---

## Task 7: SSE Client

**Files:**
- Create: `frontend/src/api/sse.js`

- [ ] **Step 1: Write SSE client using fetch + ReadableStream**

`frontend/src/api/sse.js`:
```javascript
/**
 * Send a POST request and parse SSE events from the response stream.
 * @param {string} url - API endpoint URL
 * @param {{topic: string}} body - Request body
 * @param {object} handlers - Event callbacks
 * @param {(data: object) => void} handlers.onStage - Stage start/complete
 * @param {(data: object) => void} handlers.onToken - Token received
 * @param {(data: object) => void} handlers.onDone - Pipeline complete
 * @param {(error: Error) => void} handlers.onError - Error occurred
 */
export async function fetchSSE(url, body, { onStage, onToken, onDone, onError }) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (currentEvent === 'stage' && onStage) onStage(data)
          else if (currentEvent === 'token' && onToken) onToken(data)
          else if (currentEvent === 'done' && onDone) onDone(data)
        }
      }
    }
  } catch (err) {
    if (onError) onError(err)
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/sse.js
git commit -m "feat: add SSE client with fetch+ReadableStream parsing"
```

---

## Task 8: Frontend Components

**Files:**
- Create: `frontend/src/components/TopicInput.vue`
- Create: `frontend/src/components/ContentPanel.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Write TopicInput component**

`frontend/src/components/TopicInput.vue`:
```vue
<template>
  <div class="flex gap-3">
    <input
      v-model="topic"
      @keyup.enter="handleGenerate"
      :disabled="loading"
      type="text"
      placeholder="输入主题，例如：人工智能在教育领域的应用"
      class="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400"
    />
    <button
      @click="handleGenerate"
      :disabled="loading || !topic.trim()"
      class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
    >
      <span v-if="loading" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
      {{ loading ? '生成中...' : '开始生成' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean,
})

const emit = defineEmits(['generate'])

const topic = ref('')

function handleGenerate() {
  if (topic.value.trim() && !props.loading) {
    emit('generate', topic.value.trim())
  }
}

function reset() {
  topic.value = ''
}

defineExpose({ reset })
</script>
```

- [ ] **Step 2: Write ContentPanel component**

`frontend/src/components/ContentPanel.vue`:
```vue
<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="flex border-b border-gray-200">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'px-5 py-3 text-sm font-medium border-b-2 transition-colors',
          activeTab === tab.key
            ? 'border-blue-600 text-blue-600 bg-blue-50'
            : 'border-transparent text-gray-500 hover:text-gray-700',
          tab.completed ? 'text-green-600' : '',
        ]"
      >
        <span v-if="tab.completed" class="mr-1">&#10003;</span>
        {{ tab.label }}
      </button>
    </div>
    <div class="p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
      <div v-if="!tabs.find(t => t.key === activeTab)?.content" class="text-gray-400 text-center py-12">
        {{ activeStage === activeTab ? '正在生成...' : '等待生成...' }}
      </div>
      <pre v-else class="whitespace-pre-wrap text-gray-800 text-sm leading-relaxed font-sans">{{ tabs.find(t => t.key === activeTab)?.content }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  stageData: { type: Object, required: true },
  activeStage: { type: String, default: '' },
})

const activeTab = ref('research')

const STAGES = [
  { key: 'research', label: '资料收集' },
  { key: 'outline', label: '文章大纲' },
  { key: 'content', label: '正文内容' },
  { key: 'script', label: '口播稿' },
]

const tabs = computed(() =>
  STAGES.map(s => ({
    key: s.key,
    label: s.label,
    content: props.stageData[s.key] || '',
    completed: !!props.stageData[s.key] && props.activeStage !== s.key,
  }))
)

watch(() => props.activeStage, (stage) => {
  if (stage) activeTab.value = stage
})

function reset() {
  activeTab.value = 'research'
}

defineExpose({ reset })
</script>
```

```vue
<script setup>
import { ref, watch, computed } from 'vue'
```

- [ ] **Step 3: Write App.vue**

`frontend/src/App.vue`:
```vue
<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <header class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">ScriptPilot</h1>
      <p class="text-gray-500">AI 口播稿生成器 — 输入主题，自动生成口播稿</p>
    </header>

    <TopicInput :loading="loading" @generate="handleGenerate" ref="topicInput" />

    <div v-if="hasStarted" class="mt-6">
      <ContentPanel :stageData="stageData" :activeStage="currentStage" ref="contentPanel" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import TopicInput from './components/TopicInput.vue'
import ContentPanel from './components/ContentPanel.vue'
import { fetchSSE } from './api/sse.js'

const loading = ref(false)
const hasStarted = ref(false)
const currentStage = ref('')
const stageData = reactive({
  research: '',
  outline: '',
  content: '',
  script: '',
})

const topicInput = ref(null)
const contentPanel = ref(null)

async function handleGenerate(topic) {
  loading.value = true
  hasStarted.value = true
  currentStage.value = ''
  Object.keys(stageData).forEach(k => stageData[k] = '')

  if (contentPanel.value) contentPanel.value.reset()

  await fetchSSE('/api/generate', { topic }, {
    onStage(data) {
      if (data.status === 'running') {
        currentStage.value = data.stage
      }
    },
    onToken(data) {
      stageData[data.stage] += data.token
    },
    onDone() {
      loading.value = false
      currentStage.value = ''
    },
    onError(err) {
      console.error('SSE error:', err)
      loading.value = false
    },
  })
}
</script>
```

- [ ] **Step 4: Clean up default Vue files**

Delete unnecessary files from the Vue scaffold:

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot/frontend
rm -f src/components/HelloWorld.vue src/components/TheWelcome.vue src/components/WelcomeItem.vue src/components/icons/
rm -f src/assets/base.css src/assets/logo.svg src/assets/main.css
```

Replace `frontend/src/main.js` with:

```javascript
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

- [ ] **Step 5: Commit**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
git add frontend/
git commit -m "feat: add Vue frontend components — TopicInput, ContentPanel, App with SSE integration"
```

---

## Task 9: End-to-End Integration Test

**Files:** None (verification only)

- [ ] **Step 1: Start backend**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot
DEEPSEEK_API_KEY=<your_real_key> uvicorn backend.app:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```bash
cd /Users/dadudu/idea/vibe-coding/ScriptPilot/frontend
npm run dev
```

- [ ] **Step 3: Test in browser**

1. Open `http://localhost:5173`
2. Enter a topic (e.g. "人工智能在教育中的应用")
3. Click "开始生成"
4. Verify:
   - Button shows loading state
   - "资料收集" tab activates, text streams in
   - After completion, "文章大纲" tab activates automatically
   - Same for "正文内容" and "口播稿"
   - Completed tabs show green checkmark
   - All content is readable and coherent

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup and integration verification"
```
