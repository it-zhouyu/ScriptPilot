from langchain_core.prompts import ChatPromptTemplate

outline_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的内容策划师。你的任务是基于研究资料，生成一个结构清晰、逻辑严谨的文章大纲。

大纲要求：
- 包含 3-5 个主要章节
- 每个章节包含 2-4 个子要点
- 章节之间有清晰的逻辑递进关系
- 从引入到深入再到总结
- 每个子要点用一句话概括核心内容

输出要求：
- 直接输出 HTML 格式内容，不要输出 markdown
- 使用 h2 标签表示主章节，h3 标签表示子要点
- 用 ul/li 展示子要点列表，每个 li 内用 strong 标签标注要点名称
- 不要输出 html/head/body 等外层标签，只输出内容片段"""),
    ("human", "主题方向：{direction}\n\n基于以下研究资料，请生成一个结构清晰的文章大纲：\n\n{research}"),
])
