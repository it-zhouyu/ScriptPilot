import logging
import os
from html import escape

from tavily import TavilyClient

logger = logging.getLogger("scriptpilot")

_tavily_client = None


def _get_tavily_client():
    global _tavily_client
    if _tavily_client is not None:
        return _tavily_client
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        return None
    _tavily_client = TavilyClient(api_key=key)
    return _tavily_client


def _format_result(idx: int, r: dict) -> str:
    title = escape(r.get("title", "无标题"))
    content = escape(r.get("content", ""))
    url = r.get("url", "")
    safe_url = escape(url, quote=True)
    return (
        f'<div class="search-card">'
        f'<div class="search-card-header">'
        f'<span class="search-card-index">#{idx}</span>'
        f'<span class="search-card-title">{title}</span>'
        f'</div>'
        f'<p class="search-card-content">{content}</p>'
        f'<a class="search-card-url" href="{safe_url}" target="_blank">{escape(url)}</a>'
        f'</div>'
    )


def _search(query: str) -> list[dict]:
    client = _get_tavily_client()
    if not client:
        logger.info("[research] Tavily key not set, skipping web search")
        return []
    logger.info("[research] Searching web via Tavily: %s", query)
    response = client.search(query, max_results=8, search_depth="advanced")
    results = response.get("results", [])
    logger.info("[research] Found %d results", len(results))
    return results
