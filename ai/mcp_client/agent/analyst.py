# agents/analyst.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import sys
import os

# 添加项目根目录到路径获取配置信息
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config

_PROMPT_TEMPLATE = """
{prompt}

研究资料：
{research_data}
"""

async def analyst_node(state):
    prompt_text = open("prompts/analyst_prompt.txt").read()
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", _PROMPT_TEMPLATE.format(
            prompt=prompt_text,
            research_data=state["research_data"]
        ))
    ])

    model = ChatOpenAI(
        model=config.DEEPSEEK_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        temperature=0.3
    )
    chain = prompt | model
    result = await chain.ainvoke({})
    
    return {"analysis": result.content}
