import os
import logging

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger("scriptpilot")

_api_key = os.getenv("DEEPSEEK_API_KEY", "")
_zhipu_api_key = os.getenv("ZHIPU_API_KEY", "")
_research_enabled = os.getenv("RESEARCH_ENABLED", "false").lower() in ("true", "1", "yes")
_content_enabled = os.getenv("CONTENT_ENABLED", "false").lower() in ("true", "1", "yes")


def is_research_enabled():
    return _research_enabled


def is_content_enabled():
    return _content_enabled


_llm = None
_fallback_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatDeepSeek(
            model="deepseek-v4-flash",
            api_key=_api_key,
            streaming=True,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
    return _llm


def get_fallback_llm():
    global _fallback_llm
    if _fallback_llm is None:
        _fallback_llm = ChatOpenAI(
            model="glm-5.1",
            api_key=_zhipu_api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4",
            streaming=True,
        )
    return _fallback_llm
