from backend.config import get_llm
from backend.graph.state import PipelineState
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
    async for chunk in chain.astream({
        "outline": state["outline"],
        "research": state["research"],
    }):
        if chunk.content:
            yield chunk.content
