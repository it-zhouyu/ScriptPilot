from backend.config import get_llm
from backend.graph.state import PipelineState
from backend.prompts.script import script_prompt


def script_node(state: PipelineState) -> dict:
    chain = script_prompt | get_llm()
    response = chain.invoke({"content": state["content"]})
    return {"script": response.content, "current_stage": "script"}


async def stream_script(state: PipelineState):
    chain = script_prompt | get_llm()
    async for chunk in chain.astream({"content": state["content"]}):
        if chunk.content:
            yield chunk.content
