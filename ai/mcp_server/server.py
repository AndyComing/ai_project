# mcp_server.py
"""
MCP服务器端 - 基于HTTP流式传输的测试用例代码
功能：提供MCP工具调用服务，支持流式响应和实时数据传输
作者：用户编写
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, AsyncGenerator
from fastmcp import FastMCP
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import threading

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import config

# 配置日志系统
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamMCPWrapper:
    """
    MCP服务器流式响应包装器
    
    功能：
    1. 包装原生MCP服务器，使其支持流式响应
    2. 管理请求队列和响应队列
    3. 处理异步流式数据传输
    """

    def __init__(self, mcp_app: FastMCP):
        """
        初始化流式包装器
        
        Args:
            mcp_app: FastMCP应用实例
        """
        self.mcp_app = mcp_app
        # 请求队列：存储待处理的请求
        self.request_queue = asyncio.Queue()
        # 响应队列字典：每个请求ID对应一个响应队列
        self.response_queues: Dict[str, asyncio.Queue] = {}

    async def handle_request(self, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        处理请求并返回流式响应
        
        Args:
            request_data: 请求数据字典
            
        Yields:
            str: Server-Sent Events格式的流式数据
            
        工作流程：
        1. 为每个请求创建唯一的响应队列
        2. 将请求放入处理队列
        3. 持续监听响应队列，返回流式数据
        4. 处理完成或错误时终止流
        """
        request_id = request_data.get("id", "default")
        logger.info(f"处理请求 ID: {request_id}")

        # 为当前请求创建专用的响应队列
        response_queue = asyncio.Queue()
        self.response_queues[request_id] = response_queue

        try:
            # 将请求放入队列，等待MCP工作线程处理
            await self.request_queue.put((request_id, request_data))
            logger.info(f"请求 {request_id} 已加入处理队列")

            # 持续监听响应队列，返回流式数据
            while True:
                try:
                    # 等待响应，设置30秒超时
                    response = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                    
                    # 根据响应类型处理
                    if response.get("type") == "complete":
                        # 完成响应，发送最终结果并结束流
                        yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                        logger.info(f"请求 {request_id} 处理完成")
                        break
                    elif response.get("type") == "error":
                        # 错误响应，发送错误信息并结束流
                        yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                        logger.error(f"请求 {request_id} 处理出错: {response.get('error')}")
                        break
                    else:
                        # 中间响应（如进度更新、数据块等）
                        yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                        
                except asyncio.TimeoutError:
                    # 超时处理
                    timeout_response = {'type': 'error', 'error': '请求处理超时'}
                    yield f"data: {json.dumps(timeout_response)}\n\n"
                    logger.error(f"请求 {request_id} 处理超时")
                    break
                    
        finally:
            # 清理资源：删除该请求的响应队列
            if request_id in self.response_queues:
                del self.response_queues[request_id]
                logger.info(f"清理请求 {request_id} 的响应队列")


# =============================================================================
# MCP工具定义区域
# =============================================================================

# 创建 FastMCP 应用实例
mcp = FastMCP("StreamingDemo")


@mcp.tool()
async def add_numbers(a: float, b: float) -> float:
    """
    数字相加工具 - 基础同步工具示例
    
    Args:
        a: 第一个数字
        b: 第二个数字
        
    Returns:
        float: 两数之和
        
    用途：演示基本的MCP工具调用，无流式响应
    """
    logger.info(f"执行数字相加: {a} + {b}")
    await asyncio.sleep(0.5)  # 模拟处理时间
    result = a + b
    logger.info(f"计算结果: {result}")
    return result


@mcp.tool()
async def generate_text(prompt: str, max_length: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
    """
    文本生成工具 - 流式文本生成示例
    
    Args:
        prompt: 输入提示词
        max_length: 最大生成长度（暂未使用）
        
    Yields:
        Dict: 包含生成进度的字典
        
    用途：演示流式文本生成，分块返回内容
    """
    logger.info(f"开始生成文本，提示词: {prompt}")
    
    # 模拟流式文本生成过程
    words = [
        f"这是对 '{prompt}' 的响应部分", 
        "第二部分内容", 
        "最后一部分内容"
    ]
    result = ""
    
    # 分块生成文本
    for i, word in enumerate(words):
        await asyncio.sleep(0.5)  # 模拟生成延迟
        result += word + " "
        
        # 如果不是最后一块，发送进度更新
        if i < len(words) - 1:
            chunk_data = {
                "type": "chunk", 
                "content": word, 
                "progress": f"{i + 1}/{len(words)}"
            }
            logger.info(f"发送文本块 {i + 1}: {word}")
            yield chunk_data

    # 发送最终完整结果
    complete_data = {"type": "complete", "content": result.strip()}
    logger.info(f"文本生成完成: {result.strip()}")
    yield complete_data


@mcp.tool()
async def count_to_n(n: int) -> AsyncGenerator[Dict[str, Any], None]:
    """
    计数工具 - 进度更新示例
    
    Args:
        n: 要数到的数字
        
    Yields:
        Dict: 包含计数进度的字典
        
    用途：演示长时间任务的进度更新和流式响应
    """
    logger.info(f"开始计数到 {n}")
    
    # 逐个计数并发送进度更新
    for i in range(1, n + 1):
        await asyncio.sleep(0.3)  # 模拟计数延迟
        
        progress_data = {
            "type": "progress",
            "current": i,
            "total": n,
            "percentage": f"{(i / n) * 100:.1f}%"
        }
        logger.info(f"计数进度: {i}/{n} ({(i / n) * 100:.1f}%)")
        yield progress_data

    # 发送完成消息
    complete_data = {"type": "complete", "message": f"成功数到 {n}!"}
    logger.info(f"计数完成: 成功数到 {n}")
    yield complete_data


# =============================================================================
# 主服务器应用类
# =============================================================================

class MCPServerApp:
    """
    MCP流式服务器应用主类
    
    功能：
    1. 集成FastAPI和MCP服务器
    2. 提供HTTP API接口
    3. 支持流式响应
    4. 管理异步任务处理
    """

    def __init__(self, host: str = None, port: int = None):
        """
        初始化MCP服务器应用
        
        Args:
            host: 服务器监听地址（默认使用config中的配置）
            port: 服务器监听端口（默认使用config中的配置）
        """
        self.host = host or config.HOST
        self.port = port or 8011  # MCP服务器使用不同端口避免冲突
        
        # 创建FastAPI应用
        self.app = FastAPI(
            title="MCP Streaming Server",
            description="基于HTTP流式传输的MCP服务器",
            version="1.0.0"
        )
        
        # 获取MCP应用实例和流式包装器
        self.mcp_app = mcp
        self.wrapper = StreamMCPWrapper(self.mcp_app)

        # 设置路由
        self._setup_routes()
        # 注意：工作线程将在服务器启动时启动
        logger.info(f"MCP服务器应用初始化完成，监听地址: {self.host}:{self.port}")

    def _setup_routes(self):
        """
        设置FastAPI路由
        
        包含以下路由：
        1. 根路径 - 服务状态检查
        2. 健康检查 - 服务健康状态
        3. 工具调用 - 流式工具调用接口
        4. 工具列表 - 获取可用工具信息
        """

        @self.app.get("/")
        async def root():
            """根路径 - 返回服务基本信息"""
            return {
                "message": "MCP Streaming Server is running",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/health",
                    "call_tool": "/api/call",
                    "list_tools": "/api/tools"
                }
            }

        @self.app.get("/health")
        async def health():
            """健康检查接口 - 用于监控服务状态"""
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "active_requests": len(self.wrapper.response_queues)
            }

        @self.app.post("/api/call")
        async def call_tool(request: Request):
            """
            工具调用接口 - 支持流式响应
            
            请求格式：
            {
                "id": "请求ID",
                "method": "tools/call",
                "params": {
                    "name": "工具名称",
                    "arguments": {...}
                }
            }
            
            响应：Server-Sent Events格式的流式数据
            """
            try:
                # 解析请求数据
                data = await request.json()
                logger.info(f"收到工具调用请求: {data}")

                # 验证请求格式
                if "method" not in data or "params" not in data:
                    return {"error": "请求格式错误，缺少必要字段"}

                # 返回流式响应
                return EventSourceResponse(
                    self.wrapper.handle_request(data),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
                
            except json.JSONDecodeError:
                logger.error("请求JSON解析失败")
                return {"error": "无效的JSON格式"}
            except Exception as e:
                logger.error(f"处理请求时出错: {e}")
                return {"error": str(e)}

        @self.app.get("/api/tools")
        async def list_tools():
            """
            获取可用工具列表接口
            
            返回所有已注册的MCP工具的元信息
            """
            return {
                "tools": [
                    {
                        "name": "add_numbers",
                        "description": "Add two numbers together",
                        "parameters": {
                            "a": {"type": "number", "description": "第一个数字"},
                            "b": {"type": "number", "description": "第二个数字"}
                        },
                        "example": {"a": 5, "b": 3}
                    },
                    {
                        "name": "generate_text",
                        "description": "Generate text based on a prompt",
                        "parameters": {
                            "prompt": {"type": "string", "description": "输入提示词"},
                            "max_length": {"type": "number", "optional": True, "description": "最大生成长度"}
                        },
                        "example": {"prompt": "你好世界"}
                    },
                    {
                        "name": "count_to_n",
                        "description": "Count to n with streaming updates",
                        "parameters": {
                            "n": {"type": "number", "description": "要数到的数字"}
                        },
                        "example": {"n": 5}
                    }
                ],
                "total": 3
            }

    def _start_mcp_worker(self):
        """
        启动MCP工作线程来处理请求
        
        工作流程：
        1. 从请求队列中获取待处理的请求
        2. 根据请求类型分发到相应的处理函数
        3. 处理结果通过响应队列返回给客户端
        """

        async def mcp_worker():
            """MCP工作线程主循环"""
            logger.info("MCP工作线程已启动")
            
            while True:
                try:
                    # 从请求队列获取请求
                    request_id, request_data = await self.wrapper.request_queue.get()
                    logger.info(f"工作线程处理请求: {request_id}")

                    # 根据请求方法类型分发处理
                    if request_data.get("method") == "tools/call":
                        # 工具调用请求
                        await self._handle_tool_call(request_id, request_data)
                    else:
                        # 其他类型的MCP请求（如初始化、列表工具等）
                        # 注意：这里需要根据实际的fastmcp API进行调整
                        logger.warning(f"未处理的请求类型: {request_data.get('method', 'unknown')}")
                        if request_id in self.wrapper.response_queues:
                            await self.wrapper.response_queues[request_id].put({
                                "type": "error",
                                "error": f"未支持的请求类型: {request_data.get('method', 'unknown')}"
                            })

                except Exception as e:
                    logger.error(f"MCP工作线程出错: {e}")
                    # 发送错误响应
                    if request_id in self.wrapper.response_queues:
                        await self.wrapper.response_queues[request_id].put({
                            "type": "error",
                            "error": str(e)
                        })

        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行的事件循环，直接创建任务
            loop.create_task(mcp_worker())
            logger.info("MCP工作线程已在现有事件循环中启动")
        except RuntimeError:
            # 如果没有运行的事件循环，创建一个新的事件循环来运行工作线程
            def run_worker():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.create_task(mcp_worker())
                loop.run_forever()
            
            import threading
            worker_thread = threading.Thread(target=run_worker, daemon=True)
            worker_thread.start()
            logger.info("MCP工作线程已在独立线程中启动")

    async def _handle_tool_call(self, request_id: str, request_data: Dict[str, Any]):
        """
        处理工具调用请求
        
        Args:
            request_id: 请求唯一标识符
            request_data: 请求数据字典
            
        处理流程：
        1. 解析请求参数
        2. 根据工具名称调用相应函数
        3. 处理流式和非流式响应
        4. 发送结果到响应队列
        """
        try:
            # 解析请求参数
            params = request_data.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            logger.info(f"调用工具: {tool_name}, 参数: {arguments}")

            # 根据工具名称调用相应的工具函数
            if tool_name == "add_numbers":
                # 同步工具调用
                result = await add_numbers(**arguments)
                if request_id in self.wrapper.response_queues:
                    await self.wrapper.response_queues[request_id].put({
                        "type": "complete",
                        "content": result
                    })

            elif tool_name == "generate_text":
                # 流式工具调用
                async for chunk in generate_text(**arguments):
                    if request_id in self.wrapper.response_queues:
                        await self.wrapper.response_queues[request_id].put(chunk)

            elif tool_name == "count_to_n":
                # 流式工具调用
                async for chunk in count_to_n(**arguments):
                    if request_id in self.wrapper.response_queues:
                        await self.wrapper.response_queues[request_id].put(chunk)

            else:
                # 未知工具
                error_msg = f"未知工具: {tool_name}"
                logger.warning(error_msg)
                if request_id in self.wrapper.response_queues:
                    await self.wrapper.response_queues[request_id].put({
                        "type": "error",
                        "error": error_msg
                    })

        except TypeError as e:
            # 参数类型错误
            error_msg = f"参数类型错误: {str(e)}"
            logger.error(error_msg)
            if request_id in self.wrapper.response_queues:
                await self.wrapper.response_queues[request_id].put({
                    "type": "error",
                    "error": error_msg
                })
        except Exception as e:
            # 其他异常
            error_msg = f"工具调用出错: {str(e)}"
            logger.error(error_msg)
            if request_id in self.wrapper.response_queues:
                await self.wrapper.response_queues[request_id].put({
                    "type": "error",
                    "error": error_msg
                })

    def run(self):
        """
        运行服务器
        
        启动Uvicorn ASGI服务器，提供HTTP服务
        """
        logger.info(f"启动MCP流式服务器: http://{self.host}:{self.port}")
        
        # 在服务器启动时启动工作线程
        self._start_mcp_worker()
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True
        )


# =============================================================================
# 服务器启动入口
# =============================================================================

if __name__ == "__main__":
    """
    服务器启动入口点
    
    启动MCP流式服务器，监听指定端口
    可以通过以下方式访问：
    - 服务状态: http://localhost:8011/
    - 健康检查: http://localhost:8011/health
    - 工具列表: http://localhost:8011/api/tools
    - 工具调用: http://localhost:8011/api/call
    """
    # 创建服务器实例
    server = MCPServerApp(host="0.0.0.0", port=8011)
    
    print("=" * 60)
    print("🚀 MCP流式服务器启动中...")
    print(f"📍 服务地址: http://{server.host}:{server.port}")
    print("🔧 可用接口:")
    print(f"   - 服务状态: http://{server.host}:{server.port}/")
    print(f"   - 健康检查: http://{server.host}:{server.port}/health")
    print(f"   - 工具列表: http://{server.host}:{server.port}/api/tools")
    print(f"   - 工具调用: http://{server.host}:{server.port}/api/call")
    print("=" * 60)
    
    # 启动服务器
    server.run()