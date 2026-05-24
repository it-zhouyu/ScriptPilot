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

from backend.graph.pipeline import run_pipeline_streaming
from backend.nodes.clarify import stream_clarify

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
        async for event in stream_clarify(topic):
            yield event

    return EventSourceResponse(event_generator())


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    direction = body.get("direction", "").strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)

    async def event_generator():
        async for event in run_pipeline_streaming(topic, direction):
            yield event

    return EventSourceResponse(event_generator())


# Serve Vue build output in production
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
