from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.content import content_prompt


async def stream_content(state: PipelineState):
    research = state["research"]
    has_research = bool(research and research.strip())
    async for item in stream_chain(content_prompt, {
        "direction": state.get("direction", ""),
        "outline": state["outline"],
        "style": state.get("style", ""),
        "research_hint": " 可以参考提供的研究资料来丰富内容。" if has_research else "",
        "research_requirement": "- 适当引用研究资料中的数据和案例\n" if has_research else "",
        "research_block": "以下是一些相关资料，可以参考：\n\n" + research if has_research else "",
    }):
        yield item
