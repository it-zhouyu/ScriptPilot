import json
import logging
import time
from typing import AsyncGenerator

from backend.nodes.clarify import stream_clarify
from backend.nodes.research import stream_research
from backend.nodes.outline import stream_outline
from backend.nodes.content import stream_content
from backend.nodes.script import stream_script

logger = logging.getLogger("scriptpilot")

STAGES = ["research", "outline", "content", "script"]

STREAM_FNS = {
    "research": stream_research,
    "outline": stream_outline,
    "content": stream_content,
    "script": stream_script,
}


async def run_clarify_streaming(topic: str) -> AsyncGenerator[dict, None]:
    async for event in stream_clarify(topic):
        yield event


async def run_pipeline_streaming(topic: str, direction: str = "", research: str = "", outline: str = "", content: str = "", stop_after: str = "") -> AsyncGenerator[dict, None]:
    state: dict = {
        "topic": topic,
        "direction": direction,
        "research": "",
        "outline": "",
        "content": "",
        "script": "",
        "current_stage": "",
    }

    logger.info("Pipeline started | topic: %s | direction: %s", topic, direction or "(none)")

    for stage_name in STAGES:
        # Skip research if pre-selected content provided
        if stage_name == "research" and research:
            state["research"] = research
            logger.info("[research] skipped (using pre-selected content) | %d chars", len(research))
            yield {"event": "stage", "data": json.dumps({"stage": "research", "status": "completed"})}
            continue

        # Skip outline/content if pre-filled (edited by user)
        if stage_name == "outline" and outline:
            state["outline"] = outline
            logger.info("[outline] skipped (using edited content) | %d chars", len(outline))
            yield {"event": "stage", "data": json.dumps({"stage": "outline", "status": "completed"})}
            continue

        if stage_name == "content" and content:
            state["content"] = content
            logger.info("[content] skipped (using edited content) | %d chars", len(content))
            yield {"event": "stage", "data": json.dumps({"stage": "content", "status": "completed"})}
            continue

        start = time.time()
        logger.info("[%s] started", stage_name)
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "running"})}

        full_text = ""
        async for item_type, text in STREAM_FNS[stage_name](state):
            if item_type == "thinking":
                yield {"event": "thinking", "data": json.dumps({"stage": stage_name, "token": text})}
            else:
                full_text += text
                yield {"event": "token", "data": json.dumps({"stage": stage_name, "token": text})}

        state[stage_name] = full_text

        elapsed = time.time() - start
        logger.info("[%s] completed | %.1fs | %d chars", stage_name, elapsed, len(full_text))
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "completed"})}

        if stop_after and stage_name == stop_after:
            logger.info("Pipeline paused after [%s]", stage_name)
            yield {"event": "paused", "data": json.dumps({"stage": stage_name})}
            return

    logger.info("Pipeline completed | total stages: %d", len(STAGES))
    yield {"event": "done", "data": json.dumps(state)}
