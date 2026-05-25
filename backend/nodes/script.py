from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.script import script_prompt


async def stream_script(state: PipelineState):
    chain = script_prompt | get_llm()
    async for item in stream_chain(chain, {
        "direction": state.get("direction", ""),
        "content": state["content"],
        "style": state.get("style", ""),
    }):
        yield item
