import json
import logging
import time
from typing import AsyncGenerator

logger = logging.getLogger("scriptpilot")

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


async def run_pipeline_streaming(topic: str) -> AsyncGenerator[dict, None]:
    state: dict = {
        "topic": topic,
        "research": "",
        "outline": "",
        "content": "",
        "script": "",
        "current_stage": "",
    }

    logger.info("Pipeline started | topic: %s", topic)

    for stage_name in STAGES:
        start = time.time()
        logger.info("[%s] started", stage_name)
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "running"})}

        full_text = ""
        async for item_type, text in STREAM_FNS[stage_name](state):
            if item_type == "thinking":
                yield {"event": "thinking", "data": json.dumps({"stage": stage_name, "token": text})}
            else:
                full_text += text
                yield {"event": "token", "data": json.dumps({"stage": stage_name, "token": text})}

        state[stage_name] = full_text

        elapsed = time.time() - start
        logger.info("[%s] completed | %.1fs | %d chars", stage_name, elapsed, len(full_text))
        yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "completed"})}

    logger.info("Pipeline completed | total stages: %d", len(STAGES))
    yield {"event": "done", "data": json.dumps(state)}
