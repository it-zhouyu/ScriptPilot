from langchain_core.prompts import ChatPromptTemplate

content_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位优秀的专栏作家。你的任务是基于大纲和研究资料，撰写一篇高质量的文章。

写作要求：
- 语言流畅自然，论述充分
- 每个章节展开充分，有理有据
- 适当引用研究资料中的数据和案例
- 段落之间过渡自然
- 文章总字数控制在 1500-3000 字"""),
    ("human", "请基于以下大纲和研究资料撰写完整文章：\n\n## 大纲\n{outline}\n\n## 研究资料\n{research}"),
])
