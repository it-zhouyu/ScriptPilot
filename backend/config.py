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

_smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
_smtp_port = int(os.getenv("SMTP_PORT", "465"))
_smtp_user = os.getenv("SMTP_USER", "497269678@qq.com")
_smtp_password = os.getenv("SMTP_PASSWORD", "")


def is_research_enabled():
    return _research_enabled


def is_content_enabled():
    return _content_enabled


def get_smtp_config():
    return {
        "host": _smtp_host,
        "port": _smtp_port,
        "user": _smtp_user,
        "password": _smtp_password,
    }


_llm = None
_fallback_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatDeepSeek(
            model="deepseek-v4-pro",
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
