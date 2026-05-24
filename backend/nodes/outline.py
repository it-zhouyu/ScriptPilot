from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.outline import outline_prompt


async def stream_outline(state: PipelineState):
    chain = outline_prompt | get_llm()
    async for item in stream_chain(chain, {
        "research": state["research"],
        "direction": state.get("direction", ""),
    }):
        yield item
