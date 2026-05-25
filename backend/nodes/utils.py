import logging

from backend.config import get_llm, get_fallback_llm

logger = logging.getLogger("scriptpilot")


def _extract_thinking(chunk) -> str:
    """Extract reasoning/thinking text from a streaming chunk."""
    if hasattr(chunk, 'content_blocks') and chunk.content_blocks:
        for block in chunk.content_blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                return block.get("reasoning", "")
    if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
        return chunk.additional_kwargs.get('reasoning_content') or chunk.additional_kwargs.get('reasoning') or ""
    return ""


async def _stream(chain, inputs):
    """Stream LLM chain output, yielding (type, text) tuples."""
    async for chunk in chain.astream(inputs):
        thinking = _extract_thinking(chunk)
        if thinking:
            yield ("thinking", thinking)
        if chunk.content:
            yield ("content", chunk.content)


async def stream_chain(prompt, inputs):
    """Stream LLM chain output with fallback.

    Tries the primary LLM (DeepSeek) first.
    If it fails, retries with the fallback LLM (智谱 GLM).
    """
    try:
        chain = prompt | get_llm()
        async for item in _stream(chain, inputs):
            yield item
    except Exception as e:
        logger.warning("Primary LLM failed (%s), falling back to ZhiPu GLM", e)
        chain = prompt | get_fallback_llm()
        async for item in _stream(chain, inputs):
            yield item
