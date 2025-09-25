import os
import sys
from typing import Dict, Any, List
from openai import AsyncOpenAI
import json

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config


class GraphRAGTool:
    def __init__(self):
        self.deepseek_api_key = config.DEEPSEEK_API_KEY
        self.deepseek_base_url = config.DEEPSEEK_BASE_URL
        self.deepseek_model = config.DEEPSEEK_MODEL
        self.client = AsyncOpenAI(
            api_key=self.deepseek_api_key,
            base_url=self.deepseek_base_url
        )
        
    def get_model(self, use_local: bool = False):
        """获取模型名称，使用DeepSeek模型"""
        return self.deepseek_model
    
    async def test_graphrag(self, query: str, graph_data: Dict[str, Any], use_local: bool = False) -> Dict[str, Any]:
        """GraphRAG测试用例"""
        try:
            model_name = self.get_model(use_local)
            
            # 模拟图结构数据
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            # 构建图上下文
            graph_context = f"""
            图结构信息：
            节点数量：{len(nodes)}
            边数量：{len(edges)}
            
            节点列表：{json.dumps(nodes[:5], ensure_ascii=False)}  # 显示前5个节点
            边列表：{json.dumps(edges[:5], ensure_ascii=False)}    # 显示前5条边
            """
            
            # GraphRAG查询处理
            graphrag_prompt = f"""
            基于以下图结构信息回答用户问题：
            
            {graph_context}
            
            用户问题：{query}
            
            请分析图结构中的关系，并提供基于图结构的回答。
            """
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个图结构分析专家，能够基于图数据回答问题。"},
                    {"role": "user", "content": graphrag_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "query": query,
                "graph_nodes": len(nodes),
                "graph_edges": len(edges),
                "answer": answer,
                "model_type": "deepseek"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }
    
    async def build_knowledge_graph(self, documents: List[str], use_local: bool = False) -> Dict[str, Any]:
        """构建知识图谱"""
        try:
            model_name = self.get_model(use_local)
            
            kg_prompt = f"""
            基于以下文档构建知识图谱：
            
            文档内容：
            {json.dumps(documents, ensure_ascii=False, indent=2)}
            
            请提取实体、关系和属性，并以JSON格式返回知识图谱结构。
            格式：
            {{
                "nodes": [{{"id": "实体ID", "label": "实体名称", "type": "实体类型"}}],
                "edges": [{{"source": "源实体ID", "target": "目标实体ID", "relation": "关系类型"}}]
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个知识图谱构建专家。"},
                    {"role": "user", "content": kg_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            kg_text = response.choices[0].message.content
            
            try:
                kg_data = json.loads(kg_text)
            except:
                kg_data = {"raw_result": kg_text}
            
            return {
                "success": True,
                "knowledge_graph": kg_data,
                "model_type": "deepseek"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }

# 全局工具实例
graphrag_tool = GraphRAGTool()