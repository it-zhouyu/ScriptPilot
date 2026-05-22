from backend.graph.state import PipelineState
from backend.nodes.research import llm
from backend.prompts.outline import outline_prompt


def outline_node(state: PipelineState) -> dict:
    chain = outline_prompt | llm
    response = chain.invoke({"research": state["research"]})
    return {"outline": response.content, "current_stage": "outline"}


async def stream_outline(state: PipelineState):
    chain = outline_prompt | llm
    async for chunk in chain.astream({"research": state["research"]}):
        if chunk.content:
            yield chunk.content
