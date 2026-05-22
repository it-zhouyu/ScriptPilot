import json
from typing import AsyncGenerator

from langgraph.graph import StateGraph, START, END

from backend.graph.state import PipelineState
from backend.nodes.research import research_node, stream_research
from backend.nodes.outline import outline_node, stream_outline
from backend.nodes.content import content_node, stream_content
from backend.nodes.script import script_node, stream_script

STAGES = ["research", "outline", "content", "script"]

STREAM_FNS = {
    "research": stream_research,
    "outline": stream_outline,
    "content": stream_content,
    "script": stream_script,
}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("research", research_node)
    graph.add_node("outline", outline_node)
    graph.add_node("content", content_node)
    graph.add_node("script", script_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", "outline")
    graph.add_edge("outline", "content")
    graph.add_edge("content", "script")
    graph.add_edge("script", END)
    return graph.compile()


async def run_pipeline_streaming(topic: str) -> AsyncGenerator[str, None]:
    state: dict = {
        "topic": topic,
        "research": "",
        "outline": "",
        "content": "",
        "script": "",
        "current_stage": "",
    }

    for stage_name in STAGES:
        yield f"event: stage\ndata: {json.dumps({'stage': stage_name, 'status': 'running'})}\n\n"

        full_text = ""
        async for token in STREAM_FNS[stage_name](state):
            full_text += token
            yield f"event: token\ndata: {json.dumps({'stage': stage_name, 'token': token})}\n\n"

        state[stage_name] = full_text

        yield f"event: stage\ndata: {json.dumps({'stage': stage_name, 'status': 'completed'})}\n\n"

    yield f"event: done\ndata: {json.dumps(state)}\n\n"
