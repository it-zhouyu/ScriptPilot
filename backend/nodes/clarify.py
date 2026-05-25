from backend.prompts.clarify import clarify_prompt
from backend.nodes.utils import stream_options_stage

FALLBACK_OPTIONS = [{"id": "1", "title": "继续使用当前主题"}]


async def stream_clarify(topic: str):
    async for event in stream_options_stage("clarify", clarify_prompt, {"topic": topic}, FALLBACK_OPTIONS):
        yield event
