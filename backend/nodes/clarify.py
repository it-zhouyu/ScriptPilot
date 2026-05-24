import json
import logging

from backend.config import get_llm
from backend.prompts.clarify import clarify_prompt
from backend.nodes.utils import stream_chain, stream_stage_events

logger = logging.getLogger("scriptpilot")


def _parse_options(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(text)


async def stream_clarify(topic: str):
    logger.info("[clarify] started | topic: %s", topic)
    yield {"event": "stage", "data": json.dumps({"stage": "clarify", "status": "running"})}

    chain = clarify_prompt | get_llm()
    result = {}
    aiter = stream_chain(chain, {"topic": topic})

    async for event in stream_stage_events(aiter, "clarify", result):
        yield event

    try:
        data = _parse_options(result.get("text", ""))
        logger.info("[clarify] completed | %d options generated", len(data.get("options", [])))
        yield {"event": "options", "data": json.dumps(data)}
    except Exception:
        logger.warning("[clarify] failed to parse response, returning fallback")
        yield {"event": "options", "data": json.dumps({
            "analysis": result.get("text", ""),
            "options": [{"id": "1", "title": "继续使用当前主题", "description": "不做调整，直接基于主题生成内容", "audience": "通用"}]
        })}

    yield {"event": "stage", "data": json.dumps({"stage": "clarify", "status": "waiting"})}
