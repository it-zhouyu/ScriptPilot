import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

_api_key = os.getenv("DEEPSEEK_API_KEY", "")


def get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key=_api_key,
        streaming=True,
    )
