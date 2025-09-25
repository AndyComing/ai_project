# AI Framework - 大模型应用开发框架

## 项目结构

```
ai/
├── main.py                 # FastAPI主入口
├── config.py              # 配置管理模块
├── requirements.txt        # 依赖包列表
├── env_example.txt         # 环境变量配置示例
├── start.sh               # 启动脚本
├── api/                   # API业务模块
│   ├── routes.py          # 路由管理
│   └── business.py        # 业务API实现
├── mcp_client/            # MCP客户端
│   ├── client.py          # MCP客户端核心
│   └── tools/             # 工具类
│       ├── langchain.py   # LangChain工具
│       ├── langgraph.py   # LangGraph工具
│       ├── openai_agents.py # OpenAI Agents工具
│       ├── rag.py         # RAG工具
│       └── graphrag.py    # GraphRAG工具
└── mcp_server/            # MCP服务器
    └── server.py          # MCP服务器实现
```

## 功能特性

### 1. FastAPI框架
- 主入口：`main.py`
- 配置管理：`config.py` - 统一管理所有环境变量和配置
- 路由管理：`api/routes.py`
- 业务API：`api/business.py`
- 环境配置：`.env`文件

### 2. MCP框架
- **MCP客户端**：支持调用各种AI工具
- **MCP服务器**：提供外部函数服务
  - 路由识别函数
  - 阿里云多模态服务（语音转文字、文字转语音）
  - RAG处理函数
  - GraphRAG处理函数

### 3. AI工具集成
- **LangChain & LangGraph**：链式工作流工具
- **OpenAI Agents**：智能代理框架
- **RAG & GraphRAG**：检索增强生成和图检索增强生成

### 4. 模型支持
- 支持本地模型和线上模型
- 通过环境变量配置切换

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### 文件说明
- **`env_example.txt`**: 配置模板文件，包含所有需要的配置项和示例值
- **`.env`**: 实际配置文件，包含真实的API密钥和敏感信息（不会被提交到Git）

#### 配置步骤
复制 `env_example.txt` 为 `.env` 并填入相应的API密钥：
```bash
cp env_example.txt .env
```

编辑 `.env` 文件，配置以下必要参数：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥（主要使用）
- `OPENAI_API_KEY`: OpenAI API密钥（备用）
- `ALIBABA_CLOUD_ACCESS_KEY_ID`: 阿里云访问密钥ID
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: 阿里云访问密钥Secret
- 其他配置项可根据需要修改

### 3. 配置管理
项目使用 `config.py` 统一管理所有配置：
- 自动加载 `.env` 文件
- 提供配置验证功能
- 支持默认值设置
- 提供配置信息查询接口

可以通过以下方式使用配置：
```python
from config import config

# 获取配置值
deepseek_key = config.DEEPSEEK_API_KEY
openai_key = config.OPENAI_API_KEY  # 备用
server_url = config.MCP_SERVER_URL

# 验证配置
config.validate_config()

# 获取配置信息
config_info = config.get_config_info()
```

### 4. AI模型配置
项目支持多种AI模型：
- **DeepSeek**: 主要使用的AI模型，配置`DEEPSEEK_API_KEY`
- **OpenAI**: 备用AI模型，配置`OPENAI_API_KEY`
- **本地模型**: 支持本地部署的模型

### 5. 启动服务
```bash
./start.sh
```

或者分别启动：
```bash
# 启动MCP服务器
cd mcp_server && python server.py

# 启动主应用
cd .. && python main.py
```

## API接口

### 基础接口
- `GET /` - 根路径
- `GET /config` - 获取配置信息（隐藏敏感信息）
- `GET /business/test` - 业务测试

### 工具测试接口
- `POST /business/test/mcp_connection` - 测试MCP连接
- `POST /business/test/langchain` - 测试LangChain
- `POST /business/test/langgraph` - 测试LangGraph
- `POST /business/test/openai_agents` - 测试OpenAI Agents
- `POST /business/test/rag` - 测试RAG
- `POST /business/test/graphrag` - 测试GraphRAG

### MCP服务器接口
- `POST /business/test/mcp_server` - 测试MCP服务器调用
- `POST /business/test/alibaba_cloud` - 测试阿里云服务
- `POST /business/test/rag_server` - 测试RAG服务器处理
- `POST /business/test/graphrag_server` - 测试GraphRAG服务器处理

## 服务地址
- 主应用：http://localhost:7011
- MCP服务器：http://localhost:8011
- API文档：http://localhost:7011/docs
