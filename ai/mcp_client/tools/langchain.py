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
from langchain.cache import InMemoryCache, SQLiteCache #将缓存数据存储在内存中，而不是磁盘上
import aiohttp
import json

# 添加项目根目录到路径获取配置信息
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config
from mcp_client.tools.semantic_cache import VectorStoreBackedSimilarityCache, SemanticLangChainCache
from mcp_client.tools.sqlite_cache import SqliteExactCache

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
        
        set_llm_cache(SQLiteCache())
        set_llm_cache(SemanticLangChainCache())
        self.llm = self._setup_llm()
        self.agent_executor = None
        self.tools = self._setup_tools()
        self.chat_history = []  # 仅保存用户历史问题（避免模型引用历史答案导致串题）
        # 精确缓存改为 SQLite
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.cache"))
        self.exact_cache = SqliteExactCache(os.path.join(cache_dir, "qa_cache.sqlite3"))
        # 语义缓存
        self.semantic_cache = VectorStoreBackedSimilarityCache()
    
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
            # 1) 先命中精确缓存（SQLite）
            exact = self.exact_cache.get(message)
            if exact is not None:
                return {"success": True, "response": exact, "error": None}

            # 2) 再命中语义缓存
            if self.semantic_cache:
                sem_hit = self.semantic_cache.get(message)
                if sem_hit is not None:
                    return {"success": True, "response": sem_hit, "error": None}

            # 简单的关键词匹配来调用工具
            if "天气" in message and "北京" in message:
                weather_result = get_weather.invoke({"city": "北京"})
                # 保存历史问题与缓存
                self.chat_history.append(message)
                self.exact_cache.put(message, weather_result)
                result_payload = {
                    "success": True,
                    "response": weather_result,
                    "error": None
                }
                # 写入语义缓存
                self.semantic_cache.put(message, weather_result)
                return result_payload
            elif "天气" in message:
                # 提取城市名称
                city = "北京"  # 默认城市
                for c in ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都"]:
                    if c in message:
                        city = c
                        break
                weather_result = get_weather.invoke({"city": city})
                # 保存历史问题与缓存
                self.chat_history.append(message)
                self.exact_cache.put(message, weather_result)
                result_payload = {
                    "success": True,
                    "response": weather_result,
                    "error": None
                }
                self.semantic_cache.put(message, weather_result)
                return result_payload
            elif "地点" in message or "位置" in message or "搜索" in message:
                location_result = search_location.invoke({"query": message})
                # 保存历史问题与缓存
                self.chat_history.append(message)
                self.exact_cache.put(message, location_result)
                result_payload = {
                    "success": True,
                    "response": location_result,
                    "error": None
                }
                self.semantic_cache.put(message, location_result)
                return result_payload
            else:
                # 其他问题直接使用DeepSeek大模型回答
                try:
                    # 构建包含（仅人类）历史问题的上下文，避免把历史答案塞回去导致串题
                    messages = []
                    messages.append(SystemMessage(content=(
                        "你是一个智能助手，可以帮用户查询天气和地点信息，也能回答各种问题。"
                        "请严格遵循：只回答当前这次用户消息的问题，不要复述或合并历史问题的答案。"
                        "可以参考历史问题做推理，但最终输出仅包含本次问题的答案。"
                    )))
                    # 仅附加最近的人类问题（不附加历史回答）
                    for human_msg in self.chat_history[-10:]:
                        messages.append(HumanMessage(content=f"历史问题(供参考，勿复述)：{human_msg}"))
                    # 当前用户消息
                    messages.append(HumanMessage(content=message))
                    
                    response = await self.llm.ainvoke(messages)
                    
                    # 保存历史问题与缓存
                    self.chat_history.append(message)
                    self.exact_cache.put(message, response.content)
                    
                    result_payload = {
                        "success": True,
                        "response": response.content,
                        "error": None
                    }
                    self.semantic_cache.put(message, response.content)
                    return result_payload
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

### rag结合 
# langchain_retriever.py

from langchain_core.documents import Document  # 修复过时的导入
from langchain_community.vectorstores import Chroma  # 修复过时的导入
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# 导入RAG系统
try:
    from mcp_client.RAG.rag import get_rag_system, initialize_rag
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"RAG系统不可用: {e}")

def load_qa_chain():
    """加载问答链 - 结合LlamaIndex检索和LangChain生成"""
    if not RAG_AVAILABLE:
        # 如果RAG不可用，返回模拟链
        class MockQAChain:
            def invoke(self, inputs):
                return {
                    "result": "RAG功能不可用，请检查配置",
                    "source_documents": []
                }
        return MockQAChain()
    
    try:
        # 初始化RAG系统
        if not initialize_rag():
            raise Exception("RAG系统初始化失败")
        
        rag_system = get_rag_system()
        
        class RAGQAChain:
            def __init__(self, rag_system):
                self.rag_system = rag_system
                self.llm = ChatDeepSeek(
                    model=config.DEEPSEEK_MODEL,
                    temperature=0.1,
                    api_key=config.DEEPSEEK_API_KEY,
                    base_url=config.DEEPSEEK_BASE_URL
                )
            
            def invoke(self, inputs):
                try:
                    query = inputs.get("query", "")
                    
                    # 1. 使用LlamaIndex检索相关文档
                    retrieved_docs = self.rag_system.retrieve_documents(query)
                    
                    # 2. 构建提示词
                    context = "\n\n".join([doc["text"] for doc in retrieved_docs])
                    
                    prompt = f"""基于以下上下文信息回答用户问题。

上下文信息：
{context}

用户问题：{query}

请基于上下文信息回答问题。如果上下文中没有相关信息，请说明无法找到答案。

回答："""
                    
                    # 3. 使用DeepSeek生成回答
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                    # 4. 格式化输出
                    from langchain_core.documents import Document
                    source_docs = []
                    for doc in retrieved_docs:
                        source_docs.append(Document(
                            page_content=doc["text"],
                            metadata=doc["metadata"]
                        ))
                    
                    return {
                        "result": answer,
                        "source_documents": source_docs
                    }
                    
                except Exception as e:
                    return {
                        "result": f"处理失败: {str(e)}",
                        "source_documents": []
                    }
        
        return RAGQAChain(rag_system)
        
    except Exception as e:
        # 如果出现任何错误，返回模拟chain
        class MockQAChain:
            def invoke(self, inputs):
                return {
                    "result": f"RAG功能配置错误: {str(e)}",
                    "source_documents": []
                }
        return MockQAChain()


class LlamaIndexRetriever:
    def __init__(self, index):
        self.index = index
        self.retriever = VectorIndexRetriever(index=index, similarity_top_k=3)
        self.query_engine = RetrieverQueryEngine(retriever=self.retriever)

    def get_relevant_documents(self, query: str) -> List[Document]:
        nodes = self.retriever.retrieve(query)
        docs = []
        for node in nodes:
            doc = Document(
                page_content=node.node.text,
                metadata={"score": node.score, "source": node.node.metadata.get("file_path", "unknown")}
            )
            docs.append(doc)
        return docs

    def invoke(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)
        
