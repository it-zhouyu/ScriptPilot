import logging

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


async def stream_chain(chain, inputs):
    """Stream LLM chain output, yielding (type, text) tuples.

    Yields ("thinking", text) for reasoning tokens and ("content", text) for output tokens.
    """
    async for chunk in chain.astream(inputs):
        thinking = _extract_thinking(chunk)
        if thinking:
            yield ("thinking", thinking)
        if chunk.content:
            yield ("content", chunk.content)
