import os
import sys
from typing import Dict, Any, List
from openai import AsyncOpenAI
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config import config


class RAGTool:
    def __init__(self):
        self.deepseek_api_key = config.DEEPSEEK_API_KEY
        self.deepseek_base_url = config.DEEPSEEK_BASE_URL
        self.deepseek_model = config.DEEPSEEK_MODEL
        self.client = AsyncOpenAI(
            api_key=self.deepseek_api_key,
            base_url=self.deepseek_base_url
        )
        self.vectorizer = TfidfVectorizer()
        
    def get_model(self, use_local: bool = False):
        """获取模型名称，使用DeepSeek模型"""
        return self.deepseek_model
    
    async def test_rag(self, query: str, documents: List[str], use_local: bool = False) -> Dict[str, Any]:
        """RAG测试用例"""
        try:
            model_name = self.get_model(use_local)
            
            # 步骤1：文档向量化
            if documents:
                doc_vectors = self.vectorizer.fit_transform(documents)
                query_vector = self.vectorizer.transform([query])
                
                # 计算相似度
                similarities = cosine_similarity(query_vector, doc_vectors).flatten()
                
                # 获取最相关的文档
                top_indices = np.argsort(similarities)[-3:][::-1]  # 取前3个
                relevant_docs = [documents[i] for i in top_indices]
            else:
                relevant_docs = []
            
            # 步骤2：生成回答
            context = "\n".join(relevant_docs) if relevant_docs else "无相关文档"
            
            rag_prompt = f"""
            基于以下上下文信息回答用户问题：
            
            上下文：
            {context}
            
            用户问题：{query}
            
            请基于上下文信息提供准确的回答。
            """
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手，基于提供的上下文信息回答问题。"},
                    {"role": "user", "content": rag_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "query": query,
                "relevant_docs": relevant_docs,
                "answer": answer,
                "model_type": "deepseek"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_type": "deepseek"
            }

# 全局工具实例
rag_tool = RAGTool()