# ScriptPilot

AI 口播稿生成器。输入主题，自动完成资料收集、大纲生成、内容撰写、口播稿生成，全程实时流式输出。

## 技术栈

- **后端**: Python + FastAPI + LangGraph + LangChain + DeepSeek API
- **前端**: Vue 3 + Vite + Tailwind CSS
- **通信**: SSE (Server-Sent Events) 实时流式推送

## 工作流程

```
用户输入主题 → 资料收集 → 大纲生成 → 内容撰写 → 口播稿生成
```

4 个阶段通过 LangGraph 管道顺序执行，每个阶段的结果实时流式展示在前端。支持推理模型的思考过程展示。

## 快速开始

### 1. 环境准备

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 安装后端依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

编辑 `backend/.env`，填入 DeepSeek API Key：

```text
DEEPSEEK_API_KEY=sk-your-api-key
```

### 3. 启动服务

```bash
# 启动后端（项目根目录）
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# 启动前端（新终端）
cd frontend && npm run dev
```

### 4. 使用

打开浏览器访问 http://localhost:5173，输入主题，点击"开始生成"。

## 项目结构

```
ScriptPilot/
├── backend/
│   ├── app.py                 # FastAPI 入口，SSE 端点
│   ├── config.py              # LLM 配置（模型、API Key）
│   ├── graph/
│   │   ├── state.py           # PipelineState 状态定义
│   │   └── pipeline.py        # LangGraph 工作流 + 流式编排
│   ├── nodes/
│   │   ├── research.py        # 资料收集节点
│   │   ├── outline.py         # 大纲生成节点
│   │   ├── content.py         # 内容撰写节点
│   │   ├── script.py          # 口播稿生成节点
│   │   └── utils.py           # 流式输出工具（思考过程提取）
│   ├── prompts/               # 各阶段 Prompt 模板
│   └── .env                   # API Key 配置
├── frontend/                  # Vue 3 + Vite 项目
│   └── src/
│       ├── App.vue            # 主页面
│       ├── components/
│       │   ├── TopicInput.vue      # 主题输入组件
│       │   └── ContentPanel.vue    # 内容展示（含思考过程）
│       └── api/
│           └── sse.js              # SSE 客户端
└── .env.example               # 环境变量模板
```

## 切换模型

编辑 `backend/config.py` 中的 `model` 参数：

```python
def get_llm():
    return ChatOpenAI(
        model="deepseek-v4-flash",  # 修改此处
        base_url="https://api.deepseek.com",
        ...
    )
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/generate` | SSE 流式生成，body: `{"topic": "..."}` |
| `GET` | `/api/health` | 健康检查 |

## License

MIT
