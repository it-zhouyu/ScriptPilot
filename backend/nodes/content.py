from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.content import content_prompt


def content_node(state: PipelineState) -> dict:
    chain = content_prompt | get_llm()
    response = chain.invoke({
        "outline": state["outline"],
        "research": state["research"],
    })
    return {"content": response.content, "current_stage": "content"}


async def stream_content(state: PipelineState):
    chain = content_prompt | get_llm()
    async for item in stream_chain(chain, {
        "outline": state["outline"],
        "research": state["research"],
    }):
        yield item
