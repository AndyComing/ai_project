from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os

# 确保可导入到 mcp_client 包
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # 添加 ai/ 到 sys.path

try:
    from mcp_client.tools.langchain import get_agent
    _import_error = None
except Exception as e:
    # 记录导入错误详情
    get_agent = None  # type: ignore
    _import_error = str(e)


business_router = APIRouter()


class ChatRequest(BaseModel):
    question: str


from api.response import APIResponse


@business_router.get("/health")
async def health() -> Any:
    return APIResponse.success(data={"status": "ok"})


@business_router.post("/chat")
async def chat(req: ChatRequest) -> Any:
    """接收用户问题，调用LangChain智能体并返回统一响应格式"""
    if get_agent is None:
        error_msg = f"LangChain智能体未正确加载: {_import_error}" if _import_error else "LangChain智能体未正确加载"
        return APIResponse.error(message=error_msg, code="500")

    try:
        agent = await get_agent()
        result: Dict[str, Any] = await agent.chat(req.question)

        # 统一响应格式
        payload = {
            "response": result.get("response", ""),
            **{k: v for k, v in result.items() if k not in {"response"}}
        }
        return APIResponse.success(data=payload)
    except HTTPException as e:
        # 转统一格式
        return APIResponse.error(message=str(e.detail) if hasattr(e, "detail") else str(e), code=str(e.status_code), status_code=e.status_code)
    except Exception as e:
        return APIResponse.error(message=str(e), code="500")


# ==============================
# 缓存管理接口
# ==============================

@business_router.post("/cache/clear")
async def cache_clear_all() -> Any:
    """清空精确缓存与语义缓存。"""
    try:
        from mcp_client.tools.langchain import get_agent
        agent = await get_agent()
        # 清空精确缓存
        if hasattr(agent, "exact_cache"):
            agent.exact_cache.clear()
        # 清空语义缓存
        if hasattr(agent, "semantic_cache"):
            agent.semantic_cache.clear()
        return APIResponse.success(data={"cleared": ["exact", "semantic"]})
    except Exception as e:
        return APIResponse.error(message=str(e), code="500")


@business_router.post("/cache/clear/exact")
async def cache_clear_exact() -> Any:
    try:
        from mcp_client.tools.langchain import get_agent
        agent = await get_agent()
        if hasattr(agent, "exact_cache"):
            agent.exact_cache.clear()
        return APIResponse.success(data={"cleared": ["exact"]})
    except Exception as e:
        return APIResponse.error(message=str(e), code="500")


@business_router.post("/cache/clear/semantic")
async def cache_clear_semantic() -> Any:
    try:
        from mcp_client.tools.langchain import get_agent
        agent = await get_agent()
        if hasattr(agent, "semantic_cache"):
            agent.semantic_cache.clear()
        return APIResponse.success(data={"cleared": ["semantic"]})
    except Exception as e:
        return APIResponse.error(message=str(e), code="500")


