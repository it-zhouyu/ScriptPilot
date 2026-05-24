from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.content import content_prompt


async def stream_content(state: PipelineState):
    chain = content_prompt | get_llm()
    async for item in stream_chain(chain, {
        "direction": state.get("direction", ""),
        "outline": state["outline"],
        "research": state["research"],
    }):
        yield item
