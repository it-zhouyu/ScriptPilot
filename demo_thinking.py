"""Demo: DeepSeek streaming with reasoning/thinking content via ChatDeepSeek."""

import os
import asyncio
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate

load_dotenv("backend/.env")

llm = ChatDeepSeek(
    model="deepseek-v4-pro",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    streaming=True,
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)

prompt = ChatPromptTemplate.from_messages([
    ("human", "{topic}"),
])

chain = prompt | llm


async def main():
    print("=== DeepSeek thinking demo ===\n")

    # 打印前几个 chunk 的 content_blocks 结构
    count = 0
    async for chunk in chain.astream({"topic": "用一句话解释什么是量子计算"}):
        if count < 3:
            print(f"--- chunk {count} ---")
            print(f"  type(chunk): {type(chunk).__name__}")
            print(f"  chunk.content: {repr(chunk.content[:80]) if chunk.content else 'None'}")
            if hasattr(chunk, 'content_blocks'):
                print(f"  chunk.content_blocks: {chunk.content_blocks}")
            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                print(f"  chunk.additional_kwargs: {list(chunk.additional_kwargs.keys())}")
            count += 1
            print()

    print("=== Done ===")


asyncio.run(main())
