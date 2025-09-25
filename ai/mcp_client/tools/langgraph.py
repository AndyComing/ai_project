import os
import sys
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config


class LangGraphTool:
    def __init__(self):
        self.deepseek_api_key = config.DEEPSEEK_API_KEY
        self.deepseek_base_url = config.DEEPSEEK_BASE_URL
        self.deepseek_model = config.DEEPSEEK_MODEL
        
    def get_model(self, use_local: bool = False):
        """获取模型实例，使用DeepSeek模型"""
        return ChatOpenAI(
            openai_api_key=self.deepseek_api_key,
            base_url=self.deepseek_base_url,
            model_name=self.deepseek_model,
            temperature=0.7
        )
    
    async def test_langgraph(self, query: str, use_local: bool = False) -> Dict[str, Any]:
        """LangGraph测试用例"""
        try:
            model = self.get_model(use_local)
            
            # 模拟LangGraph工作流
            # 步骤1：分析查询
            analysis_prompt = f"分析以下查询的意图：{query}"
            analysis_result = await model.ainvoke([HumanMessage(content=analysis_prompt)])
            
            # 步骤2：生成回答
            answer_prompt = f"基于分析结果生成回答：{analysis_result.content}"
            answer_result = await model.ainvoke([HumanMessage(content=answer_prompt)])
            
            return {
                "success": True,
                "analysis": analysis_result.content,
                "answer": answer_result.content,
                "model_type": "deepseek"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }

# 全局工具实例
langgraph_tool = LangGraphTool()