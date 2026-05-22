# ScriptPilot Design

## Context

用户需要一个 AI Agent，输入主题后自动完成：资料收集 → 大纲生成 → 内容撰写 → 口播稿生成。使用 LangGraph 管理工作流，DeepSeek 作为 LLM，FastAPI 后端 + Vue 3 (Vite) 前端，SSE 实时流式输出。MVP 阶段不做持久化。

## Architecture

```
User (Vue Frontend)
  │
  │ POST /api/generate {"topic": "..."}
  │ (SSE connection)
  ▼
FastAPI Backend
  │
  │ LangGraph Pipeline
  ▼
[research] → [outline] → [content] → [script]
  │              │           │          │
  └──────────────┴───────────┴──────────┘
                   │
              DeepSeek API
```

## Project Structure

```
ScriptPilot/
├── backend/
│   ├── app.py                     # FastAPI entry, SSE endpoint
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py               # PipelineState TypedDict
│   │   └── pipeline.py            # LangGraph workflow builder
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── research.py            # Research node
│   │   ├── outline.py             # Outline generation node
│   │   ├── content.py             # Content writing node
│   │   └── script.py              # Broadcasting script node
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── research.py            # Research prompt template
│   │   ├── outline.py             # Outline prompt template
│   │   ├── content.py             # Content prompt template
│   │   └── script.py              # Script prompt template
│   └── requirements.txt
├── frontend/                      # Vue 3 + Vite
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── components/
│       │   ├── TopicInput.vue     # Topic input + generate button
│       │   ├── StageProgress.vue  # Stage progress indicator
│       │   └── ContentPanel.vue   # Tab-based content display
│       └── api/
│           └── sse.js             # EventSource wrapper
└── .env.example                   # DEEPSEEK_API_KEY template
```

## State Definition

```python
class PipelineState(TypedDict):
    topic: str            # User input topic
    research: str         # Research results
    outline: str          # Generated outline
    content: str          # Full article content
    script: str           # Broadcasting script
    current_stage: str    # Current stage name for progress tracking
```

## LangGraph Workflow

Linear graph: `START → research → outline → content → script → END`

Each node:
- Receives full PipelineState
- Reads only the fields it needs
- Calls DeepSeek via ChatOpenAI with its prompt template
- Returns updated fields

No conditional branching in MVP.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve Vue build output (static files) |
| POST | `/api/generate` | SSE stream, body: `{"topic": "..."}` |
| GET | `/api/health` | Health check |

## SSE Protocol

```
event: stage        → {"stage": "research", "status": "running"}
event: token        → {"stage": "research", "token": "..."}
event: stage        → {"stage": "research", "status": "completed"}
event: stage        → {"stage": "outline", "status": "running"}
...
event: done         → Complete state with all results
```

## Frontend Design

### Layout
- **Top**: Topic input field + Generate button (disabled during generation, shows loading)
- **Bottom**: 4 tabs — Research, Outline, Content, Script
  - Active tab auto-switches to current running stage
  - Completed stages show green checkmark on tab
  - Content streams in character by character in each tab

### Tech
- Vue 3 Composition API + `<script setup>`
- EventSource API for SSE
- Tailwind CSS via CDN (no build config needed)

## DeepSeek Configuration

- `ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com")`
- API key via env var `DEEPSEEK_API_KEY`
- Each node uses a `ChatPromptTemplate` from `prompts/` module

## Prompt Summaries

1. **Research**: "You are a senior content researcher. For topic {topic}, collect: core concepts, key data, latest developments, different perspectives..."
2. **Outline**: "Based on the following research, generate a structured outline with 3-5 main sections, each with 2-3 sub-points..."
3. **Content**: "Based on the outline and research, write a complete article with fluent language and thorough discussion..."
4. **Script**: "Convert the following article into a broadcasting script: conversational tone, strong rhythm, transition phrases, suitable for reading aloud..."

## Running

```bash
# Backend
cd backend && pip install -r requirements.txt
DEEPSEEK_API_KEY=xxx uvicorn app:app --reload

# Frontend (dev)
cd frontend && npm install && npm run dev

# Frontend (build for FastAPI to serve)
cd frontend && npm run build  # outputs to backend/static/
```

## Out of Scope (MVP)

- No database or history persistence
- No user authentication
- No conditional branching in the pipeline
- No external search API integration
