import json
import logging
import re

from backend.config import get_llm, get_fallback_llm

logger = logging.getLogger("scriptpilot")

_OPTIONS_PATTERN = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)


def extract_options(full_text):
    matches = _OPTIONS_PATTERN.findall(full_text)
    for raw in reversed(matches):
        try:
            data = json.loads(raw)
            if "options" in data:
                return data
        except json.JSONDecodeError:
            continue
    return None


def _extract_thinking(chunk) -> str:
    if hasattr(chunk, 'content_blocks') and chunk.content_blocks:
        for block in chunk.content_blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                return block.get("reasoning", "")
    if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
        return chunk.additional_kwargs.get('reasoning_content') or chunk.additional_kwargs.get('reasoning') or ""
    return ""


async def _stream(chain, inputs):
    async for chunk in chain.astream(inputs):
        thinking = _extract_thinking(chunk)
        if thinking:
            yield ("thinking", thinking)
        if chunk.content:
            yield ("content", chunk.content)


def _is_retryable_error(err):
    msg = str(err).lower()
    return any(kw in msg for kw in ['timeout', 'timed out', '429', 'rate limit', 'overloaded', '503'])


async def stream_chain(prompt, inputs):
    try:
        chain = prompt | get_llm()
        async for item in _stream(chain, inputs):
            yield item
    except Exception as e:
        if _is_retryable_error(e):
            logger.warning("Primary LLM failed (%s), falling back to ZhiPu GLM", e)
            chain = prompt | get_fallback_llm()
            async for item in _stream(chain, inputs):
                yield item
        else:
            raise


_SINGLE_OPTION = re.compile(r'\{"id"\s*:\s*"[^"]*"\s*,\s*"title"\s*:\s*"[^"]*"\s*\}')


async def stream_options_stage(stage_name, prompt, inputs, fallback_options):
    logger.info("[%s] started", stage_name)
    yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "running"})}

    full_text = ""
    json_block_started = False
    emitted_count = 0

    async for item_type, text in stream_chain(prompt, inputs):
        if item_type == "thinking":
            yield {"event": "thinking", "data": json.dumps({"stage": stage_name, "token": text})}
        else:
            full_text += text
            if not json_block_started and '```json' in full_text:
                json_block_started = True
            if not json_block_started:
                yield {"event": "token", "data": json.dumps({"stage": stage_name, "token": text})}
            else:
                json_part = full_text[full_text.index('```json') + 7:]
                for m in _SINGLE_OPTION.finditer(json_part):
                    end_pos = m.end()
                    if end_pos <= emitted_count:
                        continue
                    try:
                        opt = json.loads(m.group())
                        yield {"event": "option", "data": json.dumps(opt)}
                        emitted_count = end_pos
                    except json.JSONDecodeError:
                        continue

    if emitted_count == 0:
        logger.warning("[%s] failed to parse options, returning fallback", stage_name)
        for opt in fallback_options:
            yield {"event": "option", "data": json.dumps(opt)}

    yield {"event": "stage", "data": json.dumps({"stage": stage_name, "status": "waiting"})}
