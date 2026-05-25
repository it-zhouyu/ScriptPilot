import os

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

_api_key = os.getenv("DEEPSEEK_API_KEY", "")


def get_llm():
    return ChatDeepSeek(
        model="deepseek-v4-flash",
        api_key=_api_key,
        streaming=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}},
    )
