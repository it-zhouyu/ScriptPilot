from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.script import script_prompt


async def stream_script(state: PipelineState):
    async for item in stream_chain(script_prompt, {
        "direction": state.get("direction", ""),
        "outline": state["outline"],
        "style": state.get("style", ""),
        "direction_analysis": state.get("direction_analysis", ""),
        "style_analysis": state.get("style_analysis", ""),
    }):
        yield item
