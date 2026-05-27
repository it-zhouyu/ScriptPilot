import asyncio
import json
import logging
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.utils import create_file_data

from backend.config import get_llm

logger = logging.getLogger("scriptpilot.agent")

SKILLS_DIR = Path(__file__).parent / "skills"

SYSTEM_PROMPT = (Path(__file__).parent / "AGENTS.md").read_text(encoding="utf-8")


_agent = None
_skills_files = None


def _load_skills():
    global _skills_files
    if _skills_files is not None:
        return _skills_files

    files = {}

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_md.exists():
            key = f"/skills/{skill_dir.name}/SKILL.md"
            files[key] = create_file_data(skill_md.read_text(encoding="utf-8"))
            logger.info("Loaded skill: %s", skill_dir.name)

            for f in skill_dir.iterdir():
                if f.is_file() and f.name != "SKILL.md":
                    fkey = f"/skills/{skill_dir.name}/{f.name}"
                    files[fkey] = create_file_data(f.read_text(encoding="utf-8"))

    _skills_files = files if files else None
    return _skills_files


def get_agent():
    global _agent
    if _agent is None:
        llm = get_llm()
        skills_list = ["/skills/"] if _load_skills() else []
        _agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            skills=skills_list,
        )
        logger.info("Deep agent created with model=%s, skills=%s", getattr(llm, "model", "unknown"), skills_list)
    return _agent


def _build_messages(message: str, history: list) -> list:
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append({"role": "user", "content": content})
        elif role == "assistant":
            amsg = {"role": "assistant", "content": content}
            reasoning = msg.get("reasoning") or msg.get("reasoning_content")
            if reasoning:
                amsg["reasoning_content"] = reasoning
            messages.append(amsg)
    messages.append({"role": "user", "content": message})
    return messages


async def stream_agent_chat(message: str, history: list):
    """Stream agent response as SSE events using v3 event streaming.

    Yields SSE event dicts with three event types:
    - {"event": "reasoning", "data": {"token": "..."}} — thinking process
    - {"event": "tool", "data": {"name": "...", "args": {...}}} — tool call
    - {"event": "token", "data": {"token": "..."}} — response text
    """
    agent = get_agent()
    messages = _build_messages(message, history)

    try:
        input_data = {"messages": messages}
        skills = _load_skills()
        if skills:
            input_data["files"] = skills

        stream = await agent.astream_events(input_data, version="v3")

        async for msg in stream.messages:
            queue = asyncio.Queue()
            _has_tool_calls = False
            _text_buffer = []

            async def collect_reasoning():
                async for r in msg.reasoning:
                    if r:
                        await queue.put(("reasoning", r))

            async def collect_text():
                async for t in msg.text:
                    if t:
                        await queue.put(("token", t))

            async def collect_tool_calls():
                nonlocal _has_tool_calls
                async for chunk in msg.tool_calls:
                    if chunk.get("name"):
                        _has_tool_calls = True
                        await queue.put(("_tool_detected", None))

            async def collect_all():
                await asyncio.gather(collect_reasoning(), collect_text(), collect_tool_calls())
                await queue.put(None)

            task = asyncio.create_task(collect_all())

            while True:
                item = await queue.get()
                if item is None:
                    break
                event_type, delta = item
                if event_type == "_tool_detected":
                    _text_buffer.clear()
                elif event_type == "reasoning":
                    yield {
                        "event": "reasoning",
                        "data": json.dumps({"token": delta}, ensure_ascii=False),
                    }
                elif event_type == "token":
                    if _has_tool_calls:
                        continue
                    _text_buffer.append(delta)
                    if sum(len(t) for t in _text_buffer) > 50:
                        for t in _text_buffer:
                            yield {
                                "event": "token",
                                "data": json.dumps({"token": t}, ensure_ascii=False),
                            }
                        _text_buffer.clear()

            if not _has_tool_calls and _text_buffer:
                for t in _text_buffer:
                    yield {
                        "event": "token",
                        "data": json.dumps({"token": t}, ensure_ascii=False),
                    }

            await task

    except Exception as e:
        logger.error("Agent streaming error: %s", e, exc_info=True)
        yield {
            "event": "token",
            "data": json.dumps(
                {"token": "\n\n抱歉，AI Agent 处理时出现了问题，请重试。"},
                ensure_ascii=False,
            ),
        }
