async def stream_chain(chain, inputs):
    """Stream LLM chain output, yielding (type, text) tuples.

    Yields ("thinking", text) for reasoning tokens and ("content", text) for output tokens.
    """
    async for chunk in chain.astream(inputs):
        thinking = None
        if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
            thinking = (
                chunk.additional_kwargs.get('reasoning_content')
                or chunk.additional_kwargs.get('reasoning')
            )
        if thinking:
            yield ("thinking", thinking)
        if chunk.content:
            yield ("content", chunk.content)
