import json
import logging
import re

from backend.prompts.clarify import clarify_prompt
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


async def stream_clarify(topic: str):
    logger.info("[clarify] started | topic: %s", topic)
    yield {"event": "stage", "data": json.dumps({"stage": "clarify", "status": "running"})}

    full_text = ""
    json_block_started = False

    async for item_type, text in stream_chain(clarify_prompt, {"topic": topic}):
        if item_type == "thinking":
            yield {"event": "thinking", "data": json.dumps({"stage": "clarify", "token": text})}
        else:
            full_text += text
            # Stop streaming tokens once the JSON code block starts
            if not json_block_started and '```json' in full_text:
                json_block_started = True
                continue
            if not json_block_started:
                yield {"event": "token", "data": json.dumps({"stage": "clarify", "token": text})}

    # Parse options from the JSON code block
    data = _extract_options(full_text)
    if data and "options" in data:
        logger.info("[clarify] completed | %d options generated", len(data["options"]))
        yield {"event": "options", "data": json.dumps(data)}
    else:
        logger.warning("[clarify] failed to parse options, returning fallback")
        yield {"event": "options", "data": json.dumps({
            "options": [{"id": "1", "title": "继续使用当前主题"}]
        })}

    yield {"event": "stage", "data": json.dumps({"stage": "clarify", "status": "waiting"})}
