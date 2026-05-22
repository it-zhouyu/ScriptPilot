import logging
import os
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
