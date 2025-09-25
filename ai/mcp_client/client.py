import asyncio
import json
from typing import Any, Dict, List, AsyncGenerator
import httpx
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import config

class MCPClient:
    def __init__(self):
        self.server_url = config.MCP_SERVER_URL
        self.client = httpx.AsyncClient()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP服务器工具"""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/{tool_name}",
                json=arguments
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def call_tool_stream(self, tool_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """调用MCP服务器工具（流式传输）"""
        try:
            async with self.client.stream(
                "POST",
                f"{self.server_url}/tools/{tool_name}/stream",
                json=arguments
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk
        except Exception as e:
            yield f"错误: {str(e)}\n"
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试与MCP服务器的连接（通过列出工具判断可达性）。"""
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            tools = response.json()
            return {"status": "connected", "message": "MCP Server is reachable", "tools": tools}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def list_tools(self) -> Dict[str, Any]:
        """获取可用工具列表"""
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

# 全局MCP客户端实例
mcp_client = MCPClient()
