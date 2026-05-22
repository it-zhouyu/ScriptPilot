from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.nodes.utils import stream_chain
from backend.prompts.research import research_prompt


def research_node(state: PipelineState) -> dict:
    chain = research_prompt | get_llm()
    response = chain.invoke({"topic": state["topic"]})
    return {"research": response.content, "current_stage": "research"}


async def stream_research(state: PipelineState):
    chain = research_prompt | get_llm()
    async for item in stream_chain(chain, {"topic": state["topic"]}):
        yield item
