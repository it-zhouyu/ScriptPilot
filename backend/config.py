import os
import logging

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger("scriptpilot")


def _patch_deepseek_reasoning():
    """Patch langchain internals to preserve reasoning_content across agent turns.

    Root cause: _ChatModelStreamBase._assemble_message() builds AIMessage without
    passing reasoning_content in additional_kwargs. DeepSeek's thinking mode requires
    it to be sent back on subsequent API calls, or it returns 400.

    Fix: Patch _assemble_message to inject _reasoning_acc into additional_kwargs,
    and patch _get_request_payload to include it in the API payload.
    """
    from langchain_core.language_models.chat_model_stream import _ChatModelStreamBase

    # Patch 1: Ensure _assemble_message puts reasoning_content into additional_kwargs
    _orig_assemble = _ChatModelStreamBase._assemble_message

    def _patched_assemble(self):
        msg = _orig_assemble(self)
        if self._reasoning_acc:
            msg.additional_kwargs["reasoning_content"] = self._reasoning_acc
        return msg

    _ChatModelStreamBase._assemble_message = _patched_assemble

    # Patch 2: Ensure _get_request_payload includes reasoning_content in API payload
    _orig_payload = ChatDeepSeek._get_request_payload

    def _patched_payload(self, input_, *, stop=None, **kwargs):
        payload = _orig_payload(self, input_, stop=stop, **kwargs)

        from langchain_core.messages import AIMessage

        if hasattr(input_, "to_messages"):
            lc_messages = input_.to_messages()
        elif isinstance(input_, list):
            lc_messages = input_
        else:
            return payload

        rc_values = [
            msg.additional_kwargs["reasoning_content"]
            for msg in lc_messages
            if isinstance(msg, AIMessage)
            and msg.additional_kwargs.get("reasoning_content")
        ]

        if not rc_values:
            return payload

        rc_iter = iter(rc_values)
        for payload_msg in payload["messages"]:
            if payload_msg["role"] == "assistant" and "reasoning_content" not in payload_msg:
                try:
                    payload_msg["reasoning_content"] = next(rc_iter)
                except StopIteration:
                    break

        return payload

    ChatDeepSeek._get_request_payload = _patched_payload
    logger.info("Patched reasoning_content preservation for DeepSeek thinking mode")


_patch_deepseek_reasoning()

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
