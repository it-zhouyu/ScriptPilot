from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.content import content_prompt


async def stream_content(state: PipelineState):
    async for item in stream_chain(content_prompt, {
        "direction": state.get("direction", ""),
        "outline": state["outline"],
        "research": state["research"],
        "style": state.get("style", ""),
    }):
        yield item
