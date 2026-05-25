from backend.prompts.style import style_prompt
from backend.nodes.utils import stream_options_stage

FALLBACK_OPTIONS = [
    {"id": "1", "title": "轻松对话风"},
    {"id": "2", "title": "专业讲解风"},
    {"id": "3", "title": "故事叙述风"},
]


async def stream_style(topic: str, direction: str):
    async for event in stream_options_stage("style", style_prompt, {"topic": topic, "direction": direction}, FALLBACK_OPTIONS):
        yield event
