import json
import logging
import time
from typing import AsyncGenerator

from backend.nodes.research import stream_research
from backend.nodes.outline import stream_outline
from backend.nodes.content import stream_content
from backend.nodes.script import stream_script
from backend.nodes.utils import stream_stage_events

logger = logging.getLogger("scriptpilot")

STAGES = ["research", "outline", "content", "script"]

STREAM_FNS = {
    "research": stream_research,
    "outline": stream_outline,
    "content": stream_content,
    "script": stream_script,
}


async def run_pipeline_streaming(topic: str, direction: str = "") -> AsyncGenerator[dict, None]:
    state = {
        "topic": topic,
        "direction": direction,
        "research": "",
        "outline": "",
        "content": "",
        "script": "",
    }

    logger.info("Pipeline started | topic: %s | direction: %s", topic, direction or "(none)")

    for stage_name in STAGES:
        start = time.time()
        logger.info("[%s] started", stage_name)
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "running"})}

        result = {}
        async for event in stream_stage_events(STREAM_FNS[stage_name](state), stage_name, result):
            yield event

        state[stage_name] = result.get("text", "")

        elapsed = time.time() - start
        logger.info("[%s] completed | %.1fs | %d chars", stage_name, elapsed, len(state[stage_name]))
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "completed"})}

    logger.info("Pipeline completed | total stages: %d", len(STAGES))
    yield {"event": "done", "data": json.dumps(state)}
