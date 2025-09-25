from fastapi import FastAPI
from api.routes import router
from config import config

# 验证配置
config.validate_config()

app = FastAPI(title="AI Framework", version="1.0.0")

# 注册路由
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "AI Framework is running"}

@app.get("/config")
async def get_config():
    """获取配置信息接口"""
    return config.get_config_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
