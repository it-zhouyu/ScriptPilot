# ScriptPilot

AI 短视频口播稿生成器。支持两种模式：传统模式按步骤逐步生成，Agent 模式通过对话一键完成。

## 技术栈

- **后端**: Python + FastAPI + LangChain + DeepSeek API
- **前端**: Vue 3 + Vite + Tailwind CSS
- **Agent**: deepagents 框架 + Skills 系统
- **通信**: SSE (Server-Sent Events) 实时流式推送
- **部署**: Docker 多阶段构建

## 两种模式

### 传统模式

手动逐步操作，每步可查看、编辑、确认后再继续：

```
选题策划 → 风格选择 → 讲解思路 → 口播稿
```

### Agent 模式

与 AI Agent 对话，自动按流程完成创作。Agent 内部严格遵循流程规范，每步暂停等待确认：

```
用户输入主题 → Agent 自动选题策划 → 等待选择 → 风格推荐 → 等待确认 → 讲解思路 → 等待确认 → 生成口播稿
```

## 快速开始

### Docker 部署（推荐）

```bash
# 创建 .env 配置文件
cp .env.example .env
# 编辑 .env 填入 API Key

# 构建并运行
docker build -t scriptpilot .
docker run -d --name scriptpilot -p 8000:8000 --env-file .env scriptpilot
```

访问 http://localhost:8000

### 本地开发

```bash
# 安装后端依赖
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend && npm install && cd ..

# 配置 .env（填入 API Key）

# 启动后端
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# 启动前端（新终端）
cd frontend && npm run dev
```

## 环境变量

在项目根目录 `.env` 文件中配置：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key
ZHIPU_API_KEY=your_zhipu_api_key
TAVILY_API_KEY=your_tavily_api_key
RESEARCH_ENABLED=false
CONTENT_ENABLED=false
SMTP_HOST=
SMTP_PORT=465
SMTP_USER=
SMTP_PASSWORD=
```

## 项目结构

```
ScriptPilot/
├── Dockerfile                  # Docker 多阶段构建
├── .dockerignore
├── .env                        # 环境变量配置（已 gitignore）
├── backend/
│   ├── app.py                  # FastAPI 入口，所有 API 端点
│   ├── config.py               # LLM 配置 + DeepSeek patch
│   ├── agent/                  # AI Agent 模式
│   │   ├── Agents.md           # Agent 系统提示词（流程规范）
│   │   ├── chat.py             # Agent 对话 + SSE 流式输出
│   │   └── skills/             # Agent 技能文件
│   │       ├── clarify/SKILL.md
│   │       ├── style/SKILL.md
│   │       ├── outline/SKILL.md
│   │       └── script/SKILL.md
│   ├── graph/                  # 传统模式工作流
│   ├── nodes/                  # 传统模式各阶段节点
│   ├── prompts/                # Prompt 模板
│   └── utils/                  # 工具函数
├── frontend/
│   └── src/
│       ├── App.vue             # 主页面（模式切换）
│       └── components/
│           ├── TopicInput.vue       # 首页（输入主题 + Agent 开关）
│           ├── AgentChat.vue        # Agent 对话界面
│           ├── MarkdownSplitPanel.vue
│           ├── ThinkingIndicator.vue
│           └── FeedbackModal.vue
└── tests/
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/clarify` | 选题策划（SSE） |
| `POST` | `/api/style` | 风格推荐（SSE） |
| `POST` | `/api/generate` | 生成阶段（SSE） |
| `POST` | `/api/agent/chat` | Agent 对话（SSE） |
| `POST` | `/api/feedback` | 用户反馈 |
| `GET` | `/api/config` | 功能开关配置 |

## License

MIT
