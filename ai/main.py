from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from api.routes import router
from config import config
from api.response import APIResponse

# 验证配置
config.validate_config()

app = FastAPI(title="AI Framework", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 统一异常处理：请求校验错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return APIResponse.validation_error(message="参数验证失败", data={"errors": exc.errors(), "body": exc.body})

# 统一异常处理：HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # 将 FastAPI 的 HTTPException 转为统一格式
    code = str(exc.status_code)
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    return APIResponse.error(message=message, code=code, status_code=exc.status_code)

# 统一异常处理：未捕获异常
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return APIResponse.error(message=str(exc) or "服务器内部错误", code="500")

# 注册路由
app.include_router(router)

@app.get("/")
async def root():
    return APIResponse.success(data={"message": "AI Framework is running"})

@app.get("/config")
async def get_config():
    """获取配置信息接口"""
    return APIResponse.success(data=config.get_config_info())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
