"""
语义缓存工具 - 基于向量检索的相似度缓存

设计目标：
- 为问答对构建向量化缓存，支持语义近似命中（而非完全匹配）
- 默认使用 OpenAI Embeddings，如未配置则自动降级为禁用（不报错）
- 内存级别的 FAISS 向量库，适合单机开发/调试

使用方式：
from mcp_client.tools.semantic_cache import VectorStoreBackedSimilarityCache
cache = VectorStoreBackedSimilarityCache()
answer = cache.get("北京天气怎么样？")
cache.put("北京天气怎么样？", "晴，25℃，湿度60%")
"""

from typing import Optional, List, Tuple
import os

try:
    # 向量库与嵌入模型
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
except Exception:  # 兜底：避免导入失败影响主流程
    OpenAIEmbeddings = None  # type: ignore
    FAISS = None  # type: ignore
    Document = None  # type: ignore

try:
    # LangChain 缓存接口与返回类型
    from langchain_core.caches import BaseCache, RETURN_VAL_TYPE
    from langchain_core.outputs import Generation
except Exception:
    BaseCache = object  # type: ignore
    RETURN_VAL_TYPE = list  # type: ignore
    Generation = None  # type: ignore


class VectorStoreBackedSimilarityCache:
    """基于向量检索的语义缓存。

    - 当 OPENAI_API_KEY 不存在或依赖导入失败时，缓存将自动禁用（透明降级）。
    - 命中逻辑：使用查询向量检索最近邻，设置相似度阈值（余弦相似度）判定是否命中。
    """

    def __init__(
        self,
        score_threshold: float = 0.86,
        k: int = 3,
    ) -> None:
        self.k = k
        self.score_threshold = score_threshold

        self.enabled: bool = False
        self._embeddings = None
        self._vectorstore = None

        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if OpenAIEmbeddings is None or FAISS is None or Document is None:
                return
            if not api_key:
                return

            self._embeddings = OpenAIEmbeddings(api_key=api_key)
            # 使用空集合初始化
            self._vectorstore = FAISS.from_texts([], self._embeddings)
            # 额外维护答案表（因为只索引问题）
            self._qa_store: List[Tuple[str, str]] = []
            self.enabled = True
        except Exception:
            # 任意异常都视为不可用
            self.enabled = False
            self._embeddings = None
            self._vectorstore = None

    def get(self, query: str) -> Optional[str]:
        """按语义相似命中缓存，返回命中的答案或 None。"""
        if not self.enabled or not self._vectorstore:
            return None
        try:
            # FAISS.similarity_search_with_score 返回 (Document, score)
            results = self._vectorstore.similarity_search_with_score(query, k=self.k)
            if not results:
                return None
            # FAISS score 是 L2 距离，越小越相似；这里转成相似度阈值判断
            # 简单启发：将距离映射为相似度 sim = 1 / (1 + dist)，并与阈值比较
            best_doc, best_dist = results[0]
            similarity = 1.0 / (1.0 + float(best_dist))
            if similarity >= self.score_threshold:
                # 在 QA 表中找到对应答案
                for q, a in reversed(self._qa_store):
                    if q == best_doc.page_content:
                        return a
            return None
        except Exception:
            return None

    def put(self, query: str, answer: str) -> None:
        """写入一条问答对到缓存。"""
        if not self.enabled or not self._vectorstore:
            return
        try:
            # 先追加向量库，再记录答案
            self._vectorstore.add_texts([query])
            self._qa_store.append((query, answer))
        except Exception:
            # 忽略写入异常，避免影响主流程
            return

    def clear(self) -> None:
        """清空语义缓存。"""
        if not self.enabled:
            return
        try:
            # 通过重建空索引实现清空
            self._vectorstore = FAISS.from_texts([], self._embeddings) if self._embeddings else None
            self._qa_store = []
        except Exception:
            return


class SemanticLangChainCache(BaseCache):
    """LangChain BaseCache 适配器，底层使用 VectorStoreBackedSimilarityCache。"""

    def __init__(self, semantic_cache: Optional[VectorStoreBackedSimilarityCache] = None) -> None:
        self._cache = semantic_cache or VectorStoreBackedSimilarityCache()

    # 同步查找
    def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]:  # type: ignore[override]
        if not self._cache or not self._cache.enabled:
            return None
        answer = self._cache.get(prompt)
        if answer is None:
            return None
        if Generation is None:
            return None
        return [Generation(text=answer)]  # type: ignore[return-value]

    # 同步更新
    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:  # type: ignore[override]
        if not self._cache or not self._cache.enabled:
            return
        if not return_val:
            return
        # 取第一条生成文本
        try:
            text = getattr(return_val[0], "text", None)  # type: ignore[index]
            if isinstance(text, str) and text:
                self._cache.put(prompt, text)
        except Exception:
            return

    def clear(self, **kwargs):  # type: ignore[override]
        # 简单实现：重建缓存实例
        self._cache = VectorStoreBackedSimilarityCache()


