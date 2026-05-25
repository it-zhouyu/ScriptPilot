from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.outline import outline_prompt


async def stream_outline(state: PipelineState):
    research = state["research"]
    has_research = bool(research and research.strip())
    inputs = {
        "direction": state.get("direction", ""),
        "style": state.get("style", ""),
        "direction_analysis": state.get("direction_analysis", ""),
        "style_analysis": state.get("style_analysis", ""),
        "research_hint": " 可以参考提供的研究资料来丰富内容。" if has_research else "",
        "research_block": "以下是一些相关资料，可以参考：\n\n" + research if has_research else "请直接根据主题方向梳理讲解思路。",
    }
    async for item in stream_chain(outline_prompt, inputs):
        yield item
