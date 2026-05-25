import json
import logging
from typing import AsyncGenerator

from backend.nodes.clarify import stream_clarify
from backend.nodes.outline import stream_outline
from backend.nodes.content import stream_content
from backend.nodes.script import stream_script

logger = logging.getLogger("scriptpilot")

STREAM_FNS = {
    "outline": stream_outline,
    "content": stream_content,
    "script": stream_script,
}


async def run_clarify_streaming(topic: str) -> AsyncGenerator[dict, None]:
    async for event in stream_clarify(topic):
        yield event


async def run_stage_streaming(stage_name: str, state: dict) -> AsyncGenerator[dict, None]:
    """Run a single pipeline stage, yielding SSE events."""
    logger.info("[%s] started", stage_name)
    yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "running"})}

    full_text = ""
    async for item_type, text in STREAM_FNS[stage_name](state):
        if item_type == "thinking":
            yield {"event": "thinking", "data": json.dumps({"stage": stage_name, "token": text})}
        else:
            full_text += text
            yield {"event": "token", "data": json.dumps({"stage": stage_name, "token": text})}

    logger.info("[%s] completed | %d chars", stage_name, len(full_text))
    yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "completed"})}
    yield {"event": "done", "data": json.dumps({"stage": stage_name})}
