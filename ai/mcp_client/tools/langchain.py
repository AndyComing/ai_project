#!/usr/bin/env python3
"""
LangChain智能体工具类
封装所有AI逻辑，供FastAPI调用
"""

import os
import sys
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_deepseek import ChatDeepSeek
from langchain.globals import set_llm_cache #用于设置全局的LLM缓存机制。
from langchain.cache import InMemoryCache #将缓存数据存储在内存中，而不是磁盘上
import aiohttp
import json

# 添加项目根目录到路径获取配置信息
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config

@tool
def get_weather(city: str) -> str:
    """获取城市天气信息"""
    try:
        # 示例：直接调用模拟天气数据
        return f"{city}：晴，25°C，湿度60%"
    except Exception as e:
        return f"获取天气失败：{str(e)}"

@tool
def search_location(query: str) -> str:
    """搜索地点信息"""
    try:
        # 示例：模拟地图搜索
        return f"找到地点：{query}，坐标：116.4,39.9"
    except Exception as e:
        return f"地图搜索失败：{str(e)}"

class LangChainAgent:
    """LangChain智能体封装类"""
    
    def __init__(self):
        set_llm_cache(InMemoryCache()) #使用内存缓存来存储和检索LLM的调用结果。
        self.llm = self._setup_llm()
        self.agent_executor = None
        self.tools = self._setup_tools()
        self.chat_history = []  # 添加对话历史记录
    
    def _setup_llm(self):
        """设置大模型"""
        return ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            api_key=config.DEEPSEEK_API_KEY
        )
    
    def _setup_tools(self) -> List:
        """设置工具集"""
        return [
            get_weather,
            search_location
        ]
    
    async def initialize(self):
        """初始化智能体"""
        # 创建提示词
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""你是一个智能助手，可以调用工具帮助用户。

可用工具：
- get_weather: 获取城市天气信息，参数是城市名称
- search_location: 搜索地点信息，参数是地点名称

当用户询问天气时，必须调用 get_weather 工具。
当用户询问地点时，必须调用 search_location 工具。
其他问题直接回答。

请根据用户问题选择合适的工具。"""),
            ("placeholder", "{chat_history}"), #聊天历史
            HumanMessage(content="{input}"),# 当前输入
            ("placeholder", "{agent_scratchpad}")# 记录一个思考过程 
        ])
        
        # 创建智能体
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True, # 当智能体解析用户输入或工具输出出现错误时，自动处理而不是崩溃
            max_iterations=5, # 智能体最多执行5轮对话/工具调用防止无限循环，如果5轮后还没完成就停止比如：用户问 → 智能体思考 → 调用工具 → 处理结果 → 回复用户（算1轮）
            return_intermediate_steps=True, #返回智能体执行过程中的中间步骤
            early_stopping_method="generate" #当满足停止条件时，智能体会生成最终回复
        )
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            # 简单的关键词匹配来调用工具
            if "天气" in message and "北京" in message:
                weather_result = get_weather.invoke({"city": "北京"})
                # 保存对话历史
                self.chat_history.append((message, weather_result))
                return {
                    "success": True,
                    "response": weather_result,
                    "error": None
                }
            elif "天气" in message:
                # 提取城市名称
                city = "北京"  # 默认城市
                for c in ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都"]:
                    if c in message:
                        city = c
                        break
                weather_result = get_weather.invoke({"city": city})
                # 保存对话历史
                self.chat_history.append((message, weather_result))
                return {
                    "success": True,
                    "response": weather_result,
                    "error": None
                }
            elif "地点" in message or "位置" in message or "搜索" in message:
                location_result = search_location.invoke({"query": message})
                # 保存对话历史
                self.chat_history.append((message, location_result))
                return {
                    "success": True,
                    "response": location_result,
                    "error": None
                }
            else:
                # 其他问题直接使用DeepSeek大模型回答
                try:
                    # 构建包含历史记录的上下文
                    messages = []
                    
                    # 添加系统消息
                    messages.append(SystemMessage(content="你是一个智能助手，可以帮用户查询天气和地点信息，也能回答各种问题。"))
                    
                    # 添加对话历史
                    for human_msg, ai_msg in self.chat_history[-10:]:  # 只保留最近10轮对话
                        messages.append(HumanMessage(content=human_msg))
                        messages.append(SystemMessage(content=ai_msg))
                    
                    # 添加当前用户消息
                    messages.append(HumanMessage(content=message))
                    
                    response = await self.llm.ainvoke(messages)
                    
                    # 保存对话历史
                    self.chat_history.append((message, response.content))
                    
                    return {
                        "success": True,
                        "response": response.content,
                        "error": None
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": None,
                        "error": f"DeepSeek模型调用失败: {str(e)}"
                    }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    async def batch_chat(self, messages: List[str]) -> List[Dict[str, Any]]:
        """批量处理消息"""
        results = []
        for message in messages:
            result = await self.chat(message)
            results.append(result)
        return results

# 全局智能体实例
_agent_instance: Optional[LangChainAgent] = None

async def get_agent() -> LangChainAgent:
    """获取智能体实例（单例）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LangChainAgent()
        await _agent_instance.initialize()
    return _agent_instance