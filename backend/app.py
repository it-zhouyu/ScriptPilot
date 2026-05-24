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

from backend.graph.pipeline import run_clarify_streaming, run_pipeline_streaming
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


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    research_content = body.get("research", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        async for event in run_pipeline_streaming(topic, direction, research=research_content):
            yield event

    return EventSourceResponse(event_generator())


# Serve Vue build output in production
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
