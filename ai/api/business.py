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


class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


@business_router.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


@business_router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """接收用户问题，调用LangChain智能体并返回JSON结果"""
    if get_agent is None:
        error_msg = f"LangChain智能体未正确加载: {_import_error}" if _import_error else "LangChain智能体未正确加载"
        raise HTTPException(status_code=500, detail=error_msg)

    try:
        agent = await get_agent()
        result: Dict[str, Any] = await agent.chat(req.question)

        # 统一响应格式
        return ChatResponse(
            success=result.get("success", True),
            response=result.get("response", ""),
            error=result.get("error"),
            extra={k: v for k, v in result.items() if k not in {"success", "response", "error"}}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


