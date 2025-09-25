#!/bin/bash

# 启动MCP服务器
echo "启动MCP服务器..."
cd /Users/andy/Desktop/AIFrameWork/ai/mcp_server
python server.py &
MCP_SERVER_PID=$!

# 等待MCP服务器启动
sleep 3

# 启动主应用
echo "启动主应用..."
cd /Users/andy/Desktop/AIFrameWork/ai
python main.py &
MAIN_APP_PID=$!

echo "MCP服务器PID: $MCP_SERVER_PID"
echo "主应用PID: $MAIN_APP_PID"
echo "MCP服务器运行在: http://localhost:8001"
echo "主应用运行在: http://localhost:8000"
echo "按Ctrl+C停止所有服务"

# 等待用户中断
wait
