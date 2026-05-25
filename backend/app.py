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

from backend.graph.pipeline import run_stage_streaming
from backend.nodes.clarify import stream_clarify
from backend.nodes.style import stream_style
from backend.config import is_research_enabled, is_content_enabled
from backend.nodes.research import _format_result, _search

app = FastAPI(title="ScriptPilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(stream):
    return EventSourceResponse(event async for event in stream)


def _get_topic(body):
    topic = body.get("topic", "").strip()
    if not topic:
        return None, JSONResponse({"error": "topic is required"}, status_code=400)
    return topic, None


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def config():
    return {"researchEnabled": is_research_enabled(), "contentEnabled": is_content_enabled()}


@app.post("/api/clarify")
async def clarify(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    return _sse(stream_clarify(topic))


@app.post("/api/research")
async def research(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    direction = body.get("direction", "").strip()

    async def event_generator():
        yield {"event": "stage", "data": json.dumps({"stage": "research", "status": "running"})}

        query = f"{topic} {direction}" if direction else topic
        results = _search(query)

        if not results:
            yield {"event": "results", "data": json.dumps({"results": []})}
        else:
            cards = [
                {
                    "index": i + 1,
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "html": _format_result(i + 1, r),
                }
                for i, r in enumerate(results)
            ]
            yield {"event": "results", "data": json.dumps({"results": cards})}

        yield {"event": "stage", "data": json.dumps({"stage": "research", "status": "completed"})}

    return EventSourceResponse(event_generator())


@app.post("/api/outline")
async def outline(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    state = {
        "topic": topic,
        "direction": body.get("direction", "").strip(),
        "research": body.get("research", "").strip(),
        "style": body.get("style", "").strip(),
        "outline": "", "content": "", "script": "",
    }
    return _sse(run_stage_streaming("outline", state))


@app.post("/api/style")
async def style(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    direction = body.get("direction", "").strip()
    return _sse(stream_style(topic, direction))


@app.post("/api/content")
async def content(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    state = {
        "topic": topic,
        "direction": body.get("direction", "").strip(),
        "research": body.get("research", "").strip(),
        "outline": body.get("outline", "").strip(),
        "script": body.get("script", "").strip(),
        "style": body.get("style", "").strip(),
        "content": "",
    }
    return _sse(run_stage_streaming("content", state))


@app.post("/api/script")
async def script(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    state = {
        "topic": topic,
        "direction": body.get("direction", "").strip(),
        "research": "",
        "outline": body.get("outline", "").strip(),
        "content": "",
        "script": "",
        "style": body.get("style", "").strip(),
    }
    return _sse(run_stage_streaming("script", state))


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
