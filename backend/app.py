import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from backend.graph.pipeline import run_clarify_streaming, run_style_streaming, run_stage_streaming
from backend.config import is_research_enabled, is_content_enabled
from backend.nodes.research import _build_query, _format_result, _search

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


@app.get("/api/config")
async def config():
    return {"researchEnabled": is_research_enabled(), "contentEnabled": is_content_enabled()}


# 分析主题，生成创作方向选项
@app.post("/api/clarify")
async def clarify(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        async for event in run_clarify_streaming(topic):
            yield event

    return EventSourceResponse(event_generator())


# 搜索相关资料，返回资料卡片列表
@app.post("/api/research")
async def research(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        yield {"event": "stage", "data": json.dumps({"stage": "research", "status": "running"})}

        query = f"{topic} {direction}" if direction else topic
        results = _search(query)

        if not results:
            yield {"event": "results", "data": json.dumps({"results": []})}
        else:
            cards = []
            for i, r in enumerate(results):
                cards.append({
                    "index": i + 1,
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "html": _format_result(i + 1, r),
                })
            yield {"event": "results", "data": json.dumps({"results": cards})}

        yield {"event": "stage", "data": json.dumps({"stage": "research", "status": "completed"})}

    return EventSourceResponse(event_generator())


# 生成讲解大纲
# 入参：topic（主题）、direction（创作方向）、research（选中的资料 HTML）、style（口播风格）
# SSE 事件：stage/status、thinking、token、done
@app.post("/api/outline")
async def outline(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    research = body.get("research", "").strip()
    style = body.get("style", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    state = {"topic": topic, "direction": direction, "research": research, "style": style, "outline": "", "content": "", "script": ""}

    async def event_generator():
        async for event in run_stage_streaming("outline", state):
            yield event

    return EventSourceResponse(event_generator())


# 分析主题方向，生成口播风格选项
# 入参：topic（主题）、direction（创作方向）
# SSE 事件：thinking、token、options、done
@app.post("/api/style")
async def style(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        async for event in run_style_streaming(topic, direction):
            yield event

    return EventSourceResponse(event_generator())


# 生成自媒体文章
# 入参：topic（主题）、direction（创作方向）、research（资料）、outline（用户编辑后的大纲）、script（口播稿）、style（口播风格）
# SSE 事件：stage/status、thinking、token、done
@app.post("/api/content")
async def content(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    research = body.get("research", "").strip()
    outline = body.get("outline", "").strip()
    script = body.get("script", "").strip()
    style = body.get("style", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    state = {"topic": topic, "direction": direction, "research": research, "outline": outline, "script": script, "style": style, "content": ""}

    async def event_generator():
        async for event in run_stage_streaming("content", state):
            yield event

    return EventSourceResponse(event_generator())


# 生成字幕版口播稿
# 入参：topic（主题）、direction（创作方向）、outline（用户编辑后的大纲）、style（口播风格）
# SSE 事件：stage/status、thinking、token、done
@app.post("/api/script")
async def script(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    outline = body.get("outline", "").strip()
    style = body.get("style", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    state = {"topic": topic, "direction": direction, "research": "", "outline": outline, "content": "", "script": "", "style": style}

    async def event_generator():
        async for event in run_stage_streaming("script", state):
            yield event

    return EventSourceResponse(event_generator())


# 生产环境：托管 Vue 构建产物
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
