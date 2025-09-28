from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
from mcp_client.tools.state import MarketResearchState
from schemas.response_model import ResearchResponse
import re
from mcp_client.tools.langgraph import build_graph
# 确保可导入到 mcp_client 包
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # 添加 ai/ 到 sys.path

try:
    from mcp_client.tools.langchain import get_agent
    _import_error = None
except Exception as e:
    # 记录导入错误详情
    get_agent = None  # type: ignore
    _import_error = str(e)

# 初始化图
graph = build_graph()

class QueryRequest(BaseModel):
    query: str
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

@business_router.post("/analyze", response_model=ResearchResponse)
async def analyze_market(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    initial_state: MarketResearchState = {
        "query": request.query,
        "research_data": "",
        "analysis": "",
        "draft_report": "",
        "final_report": None,
        "trends": [],
        "sources": [],
        "revision_count": 0,
        "feedback": ""
    }

    try:
        # 执行整个流程
        async for output in graph.astream(initial_state):
            pass  # 流式输出可用于日志追踪

        # 获取最终状态
        final_output = list(output.values())[-1]

        # 使用 LLM 提取5个独立趋势
        raw_text = final_output.get("draft_report", "")
        
        # 调用 LangChain 智能体提取趋势
        try:
            from mcp_client.tools.langchain import get_agent
            agent = await get_agent()
            
            trend_extraction_prompt = f"""
            请基于以下分析报告，提取出5个独立的市场趋势，每个趋势包含：
            1. topic: 趋势主题（简洁明确，不超过20字）
            2. description: 趋势描述（详细说明，不超过80字）
            3. data_support: 数据支撑（具体数据或事实，不超过60字）
            
            分析报告内容：
            {raw_text}
            
            请以JSON格式返回，格式如下：
            [
                {{
                    "topic": "趋势主题1",
                    "description": "趋势描述1",
                    "data_support": "数据支撑1"
                }},
                {{
                    "topic": "趋势主题2", 
                    "description": "趋势描述2",
                    "data_support": "数据支撑2"
                }},
                ...
            ]
            
            请确保返回5个不同的趋势，每个趋势都要有独特性和价值。
            """
            
            trend_result = await agent.chat(trend_extraction_prompt)
            trend_response = trend_result.get("response", "")
            
            # 尝试解析JSON格式的趋势数据
            import json
            try:
                # 提取JSON部分（去除可能的markdown格式）
                if "```json" in trend_response:
                    json_start = trend_response.find("```json") + 7
                    json_end = trend_response.find("```", json_start)
                    json_str = trend_response[json_start:json_end].strip()
                elif "```" in trend_response:
                    json_start = trend_response.find("```") + 3
                    json_end = trend_response.find("```", json_start)
                    json_str = trend_response[json_start:json_end].strip()
                else:
                    json_str = trend_response.strip()
                
                trends = json.loads(json_str)
                
                # 确保不超过5个趋势
                if len(trends) > 5:
                    # 如果超过5个，只取前5个
                    trends = trends[:5]
                    
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回空数组
                trends = []
                
        except Exception as e:
            # 如果LLM调用失败，返回空数组
            trends = []

        return ResearchResponse(
            title=f"{request.query}分析报告",
            query=request.query,
            trends=trends,
            conclusion=raw_text[:500] + "...",
            sources=final_output.get("sources", [])[:5]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
