import logging
import os

from tavily import TavilyClient

from backend.graph.state import PipelineState

logger = logging.getLogger("scriptpilot")


def _format_result(idx: int, r: dict) -> str:
    title = r.get("title", "无标题")
    content = r.get("content", "")
    url = r.get("url", "")
    return (
        f'<div class="search-card">'
        f'<div class="search-card-header">'
        f'<span class="search-card-index">#{idx}</span>'
        f'<span class="search-card-title">{title}</span>'
        f'</div>'
        f'<p class="search-card-content">{content}</p>'
        f'<a class="search-card-url" href="{url}" target="_blank">{url}</a>'
        f'</div>'
    )


def _search(query: str) -> list[dict]:
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        logger.info("[research] Tavily key not set, skipping web search")
        return []
    logger.info("[research] Searching web via Tavily: %s", query)
    client = TavilyClient(api_key=key)
    response = client.search(query, max_results=8, search_depth="advanced")
    results = response.get("results", [])
    logger.info("[research] Found %d results", len(results))
    return results


def _build_query(state: PipelineState) -> str:
    topic = state.get("topic", "")
    direction = state.get("direction", "")
    return f"{topic} {direction}" if direction else topic


async def stream_research(state: PipelineState):
    results = _search(_build_query(state))
    if not results:
        yield ("content", "<p>未找到搜索结果，请检查 Tavily API Key 配置。</p>")
        return
    yield ("content", '<h2>搜索结果</h2>')
    for i, r in enumerate(results):
        yield ("content", _format_result(i + 1, r))
