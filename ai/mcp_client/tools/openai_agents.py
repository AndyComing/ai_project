import sys
import os
from typing import Dict, Any, List
from openai import AsyncOpenAI
import json

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config

class DeepSeekAgentsTool:
    def __init__(self):
        self.deepseek_api_key = config.DEEPSEEK_API_KEY
        self.deepseek_base_url = config.DEEPSEEK_BASE_URL
        self.deepseek_model = config.DEEPSEEK_MODEL
        
        # 使用DeepSeek客户端
        if self.deepseek_api_key:
            self.client = AsyncOpenAI(
                api_key=self.deepseek_api_key,
                base_url=self.deepseek_base_url
            )
        else:
            self.client = None
        
    def get_model(self, use_local: bool = False):
        """获取模型名称，使用DeepSeek模型"""
        return self.deepseek_model
    
    async def test_agents(self, task: str, use_local: bool = False) -> Dict[str, Any]:
        """DeepSeek Agents框架测试用例"""
        try:
            # 检查配置
            if not self.client:
                return {
                    "success": False,
                    "error": "DeepSeek API Key未配置",
                    "model_type": "deepseek"
                }
            
            model_name = self.get_model(use_local)
            
            # 模拟Agents工作流
            # 步骤1：创建Agent
            agent_prompt = f"""
            你是一个智能助手，需要完成以下任务：{task}
            
            请按照以下步骤进行：
            1. 分析任务需求
            2. 制定执行计划
            3. 执行任务
            4. 总结结果
            
            请以JSON格式返回结果。
            """
            
            # 调用模型
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的任务执行助手。"},
                    {"role": "user", "content": agent_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # 尝试解析JSON结果
            try:
                result_json = json.loads(result_text)
            except:
                result_json = {"raw_result": result_text}
            
            return {
                "success": True,
                "result": result_json,
                "model_type": "deepseek",
                "model_name": model_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }
    
    async def create_agent_workflow(self, workflow_config: Dict[str, Any], use_local: bool = False) -> Dict[str, Any]:
        """创建Agent工作流"""
        try:
            model_name = self.get_model(use_local)
            
            workflow_prompt = f"""
            根据以下配置创建Agent工作流：
            {json.dumps(workflow_config, ensure_ascii=False, indent=2)}
            
            请返回工作流的执行计划。
            """
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个工作流设计专家。"},
                    {"role": "user", "content": workflow_prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            return {
                "success": True,
                "workflow_plan": response.choices[0].message.content,
                "model_type": "deepseek"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }

# 全局工具实例
openai_agents_tool = DeepSeekAgentsTool()