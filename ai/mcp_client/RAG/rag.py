import os
import sys
# 添加项目根目录到路径获取配置信息
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
import chromadb

from config import config

class RAGSystem:
    """RAG检索系统 - 使用LlamaIndex"""
    
    def __init__(self):
        self.index = None
        self.query_engine = None
        self.retriever = None
        self.embed_model = None
        self.vector_store = None
        self.llm = None
        
    def initialize(self):
        """初始化RAG系统"""
        try:
            # 1. 设置Embedding模型
            self.embed_model = HuggingFaceEmbedding(
                model_name=getattr(config, 'EMBEDDING_MODEL', 'BAAI/bge-small-en-v1.5')
            )
            Settings.embed_model = self.embed_model
            
            # 2. 设置LLM（DeepSeek）
            # self.llm = OpenAI(
            #     model=config.DEEPSEEK_MODEL,
            #     api_key=config.DEEPSEEK_API_KEY,
            #     base_url=config.DEEPSEEK_BASE_URL,
            #     temperature=0.1
            # )
            
            # 确保全局设置也使用这个LLM
            # Settings.llm = self.llm
            print("✓ Embedding模型和LLM初始化成功")
            
            # 3. 加载文档 - 使用docs目录（稳健版，带回退）
            docs_dir = os.path.join(os.path.dirname(__file__), "docs")
            if not os.path.isdir(docs_dir):
                print(f"错误: 文档目录不存在: {docs_dir}")
                return False

            # 优先用 LlamaIndex 读取
            from llama_index.core import Document
            reader = SimpleDirectoryReader(
                input_dir=docs_dir,
                recursive=False,
                required_exts=[".txt"],
                filename_as_id=True,
            )
            documents = reader.load_data()

            # 兼容不同版本字段名，提取正文
            def _doc_text(d: Document) -> str:
                try:
                    return (d.get_content() or "").strip()
                except Exception:
                    return (getattr(d, "text", "") or "").strip()

            # 如果读到的文本都为空，则手动回退用原生文件读取
            if not any(_doc_text(d) for d in documents):
                txt_files = [
                    os.path.join(docs_dir, f)
                    for f in os.listdir(docs_dir)
                    if f.lower().endswith(".txt")
                ]
                documents = []
                for fp in txt_files:
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        if content:
                            documents.append(Document(text=content, metadata={"file_path": fp}))
                    except Exception:
                        continue

            if not documents:
                print("错误: 文档内容为空，无法建立索引")
                return False

            print(f"✓ 成功加载 {len(documents)} 个非空文档")
            
            # 4. 初始化Chroma向量数据库
            chroma_path = os.path.join(os.path.dirname(__file__), "../../chroma_db")
            os.makedirs(chroma_path, exist_ok=True)  # 确保目录存在
            
            db = chromadb.PersistentClient(path=chroma_path)
            
            # 确保每次初始化都用最新文档：先删后建，避免旧数据残留
            try:
                db.delete_collection("knowledge_base")
            except Exception:
                pass
            chroma_collection = db.get_or_create_collection("knowledge_base")
            self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            print("✓ Chroma向量数据库初始化成功")
            
            # 5. 构建存储上下文
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            # 6. 构建向量索引
            if documents:
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    show_progress=True
                )
            else:
                # 创建一个空索引
                self.index = VectorStoreIndex([], storage_context=storage_context)
            print("✓ 向量索引构建完成")
            
            # 7. 创建检索器
            self.retriever = VectorIndexRetriever(
                index=self.index, 
                similarity_top_k=3
            )
            
            # 8. 创建查询引擎 - 使用正确的方法避免参数冲突
            self.query_engine = None  # 让 query() 自己检索并生成
            print("✓ RAG系统初始化完成")
            return True
            
        except Exception as e:
            print(f"RAG系统初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve_documents(self, query: str, top_k: int = 3):
        """检索相关文档"""
        if not self.retriever:
            return []
        
        try:
            nodes = self.retriever.retrieve(query)
            return [
                {
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata
                }
                for node in nodes[:top_k]
            ]
        except Exception as e:
            print(f"文档检索失败: {e}")
            return []
    
    def query(self, question: str):
        """使用RAG系统回答问题"""
        if not self.retriever:
            return {"answer": "RAG系统未初始化", "sources": []}
        
        try:
            nodes = self.retriever.retrieve(question)
            def _node_text(n):
                return (getattr(getattr(n, "node", None), "get_content", lambda: "")() or
                        getattr(getattr(n, "node", None), "text", "")).strip()

            context = "\n\n".join([t for t in (_node_text(n) for n in nodes) if t])

            sources = [
                {
                    "content": _node_text(n),
                    "score": getattr(n, "score", 0.0),
                    "metadata": getattr(getattr(n, "node", None), "metadata", {}) or {}
                } for n in nodes
            ]

            prompt = f"基于以下上下文回答问题；没有相关信息请直接说明。\n\n上下文：\n{context}\n\n问题：{question}\n\n回答："

            llm = ChatDeepSeek(
                model=config.DEEPSEEK_MODEL,
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL,
                temperature=0.1
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            answer = getattr(resp, "content", str(resp))

            return {"answer": answer, "sources": sources}
        except Exception as e:
            return {"answer": f"查询失败: {str(e)}", "sources": []}

# 全局RAG系统实例
rag_system = RAGSystem()

# 初始化函数
def initialize_rag():
    """初始化RAG系统"""
    return rag_system.initialize()

# 获取RAG系统的便捷函数
def get_rag_system():
    """获取RAG系统实例"""
    return rag_system
