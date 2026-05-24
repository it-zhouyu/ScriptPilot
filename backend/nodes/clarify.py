import json
import logging

from backend.config import get_llm
from backend.prompts.clarify import clarify_prompt
from backend.nodes.utils import stream_chain

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
    full_text = ""

    async for item_type, text in stream_chain(chain, {"topic": topic}):
        if item_type == "thinking":
            yield {"event": "thinking", "data": json.dumps({"stage": "clarify", "token": text})}
        else:
            full_text += text

    try:
        data = _parse_options(full_text)
        logger.info("[clarify] completed | %d options generated", len(data.get("options", [])))
        yield {"event": "options", "data": json.dumps(data)}
    except Exception:
        logger.warning("[clarify] failed to parse response, returning fallback")
        yield {"event": "options", "data": json.dumps({
            "analysis": full_text,
            "options": [{"id": "1", "title": "继续使用当前主题", "description": "不做调整，直接基于主题生成内容", "audience": "通用"}]
        })}

    yield {"event": "stage", "data": json.dumps({"stage": "clarify", "status": "waiting"})}
