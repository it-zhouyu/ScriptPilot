import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form

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
from backend.config import is_research_enabled, is_content_enabled, get_smtp_config
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
        "direction_analysis": body.get("directionAnalysis", "").strip(),
        "style_analysis": body.get("styleAnalysis", "").strip(),
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
    direction_analysis = body.get("directionAnalysis", "").strip()
    return _sse(stream_style(topic, direction, direction_analysis))


@app.post("/api/content")
async def content(request: Request):
    body = await request.json()
    topic, err = _get_topic(body)
    if err:
        return err
    state = {
        "topic": topic,
        "direction": body.get("direction", "").strip(),
        "direction_analysis": body.get("directionAnalysis", "").strip(),
        "style_analysis": body.get("styleAnalysis", "").strip(),
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
        "direction_analysis": body.get("directionAnalysis", "").strip(),
        "style_analysis": body.get("styleAnalysis", "").strip(),
        "research": "",
        "outline": body.get("outline", "").strip(),
        "content": "",
        "script": "",
        "style": body.get("style", "").strip(),
    }
    return _sse(run_stage_streaming("script", state))


@app.post("/api/feedback")
async def feedback(
    text: str = Form(""),
    images: list[UploadFile] = File(default=[]),
):
    cfg = get_smtp_config()
    if not cfg["password"]:
        return JSONResponse({"error": "SMTP not configured"}, status_code=500)

    msg = MIMEMultipart("related")
    msg["Subject"] = "ScriptPilot 用户反馈"
    msg["From"] = cfg["user"]
    msg["To"] = "497269678@qq.com"

    body = f"<p style='white-space:pre-wrap;'>{text}</p>"
    html_part = MIMEText(f"<html><body>{body}</body></html>", "html", "utf-8")
    msg.attach(html_part)

    for img in images:
        if img.content_type and img.content_type.startswith("image/"):
            data = await img.read()
            part = MIMEImage(data)
            part.add_header("Content-ID", f"<{img.filename}>")
            part.add_header("Content-Disposition", "attachment", filename=img.filename)
            msg.attach(part)

    try:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as server:
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
        return {"status": "ok"}
    except Exception as e:
        logging.getLogger("scriptpilot").error("Feedback email failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
