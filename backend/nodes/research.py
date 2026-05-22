import os
from langchain_openai import ChatOpenAI
from backend.graph.state import PipelineState
from backend.prompts.research import research_prompt

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    streaming=True,
)


def research_node(state: PipelineState) -> dict:
    chain = research_prompt | llm
    response = chain.invoke({"topic": state["topic"]})
    return {"research": response.content, "current_stage": "research"}


async def stream_research(state: PipelineState):
    chain = research_prompt | llm
    async for chunk in chain.astream({"topic": state["topic"]}):
        if chunk.content:
            yield chunk.content
