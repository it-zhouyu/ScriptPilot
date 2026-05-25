from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.outline import outline_prompt


async def stream_outline(state: PipelineState):
    async for item in stream_chain(outline_prompt, {
        "research": state["research"],
        "direction": state.get("direction", ""),
        "style": state.get("style", ""),
    }):
        yield item
