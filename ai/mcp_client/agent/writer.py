# agents/writer.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import sys
import os

# 添加项目根目录到路径获取配置信息
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config

async def writer_node(state):
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "writer_prompt.txt")
    prompt_text = open(prompt_path).read()
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "请基于以下分析撰写报告：\n\n{analysis}")
    ])

    model = ChatOpenAI(
        model=config.DEEPSEEK_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        temperature=0.5
    )
    chain = prompt | model
    result = await chain.ainvoke({"analysis": state["analysis"]})
    
    return {"draft_report": result.content}
