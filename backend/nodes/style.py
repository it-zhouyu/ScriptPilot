import json
import logging
import re

from backend.config import get_llm
from backend.prompts.style import style_prompt
from backend.nodes.utils import stream_chain

logger = logging.getLogger("scriptpilot")

_OPTIONS_PATTERN = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)


def _extract_options(full_text):
    """Extract options JSON from the markdown code block at the end."""
    matches = _OPTIONS_PATTERN.findall(full_text)
    for raw in reversed(matches):
        try:
            data = json.loads(raw)
            if "options" in data:
                return data
        except json.JSONDecodeError:
            continue
    return None


async def stream_style(direction: str, content: str):
    logger.info("[style] started")
    yield {"event": "stage", "data": json.dumps({"stage": "style", "status": "running"})}

    chain = style_prompt | get_llm()
    full_text = ""
    json_block_started = False

    async for item_type, text in stream_chain(chain, {"direction": direction, "content": content}):
        if item_type == "thinking":
            yield {"event": "thinking", "data": json.dumps({"stage": "style", "token": text})}
        else:
            full_text += text
            if not json_block_started and '```json' in full_text:
                json_block_started = True
                continue
            if not json_block_started:
                yield {"event": "token", "data": json.dumps({"stage": "style", "token": text})}

    data = _extract_options(full_text)
    if data and "options" in data:
        logger.info("[style] completed | %d options generated", len(data["options"]))
        yield {"event": "options", "data": json.dumps(data)}
    else:
        logger.warning("[style] failed to parse options, returning fallback")
        yield {"event": "options", "data": json.dumps({
            "options": [
                {"id": "1", "title": "轻松对话风"},
                {"id": "2", "title": "专业讲解风"},
                {"id": "3", "title": "故事叙述风"},
            ]
        })}

    yield {"event": "stage", "data": json.dumps({"stage": "style", "status": "waiting"})}
