import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，用于管理所有环境变量和配置信息"""
    
    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # 阿里云配置
    ALIBABA_CLOUD_ACCESS_KEY_ID: Optional[str] = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: Optional[str] = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    ALIBABA_CLOUD_REGION: Optional[str] = os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou")
    
    # 高德地图配置
    AMAP_API_KEY: Optional[str] = os.getenv("AMAP_API_KEY")
    
    # MCP配置
    MCP_SERVER_URL: Optional[str] = os.getenv("MCP_SERVER_URL", "http://localhost:8011")
    MCP_CLIENT_URL: Optional[str] = os.getenv("MCP_CLIENT_URL", "http://localhost:8002")
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "7011"))
    
    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证必要的配置是否存在"""
        # 需要DeepSeek配置
        required_configs = [
            ("DEEPSEEK_API_KEY", cls.DEEPSEEK_API_KEY),
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"警告: 以下配置项缺失: {', '.join(missing_configs)}")
            return False
        
        return True
    
    @classmethod
    def get_config_info(cls) -> dict:
        """获取配置信息（隐藏敏感信息）"""
        return {
            "deepseek_api_key": "***" if cls.DEEPSEEK_API_KEY else None,
            "deepseek_base_url": cls.DEEPSEEK_BASE_URL,
            "deepseek_model": cls.DEEPSEEK_MODEL,
            "alibaba_cloud_access_key_id": "***" if cls.ALIBABA_CLOUD_ACCESS_KEY_ID else None,
            "alibaba_cloud_access_key_secret": "***" if cls.ALIBABA_CLOUD_ACCESS_KEY_SECRET else None,
            "alibaba_cloud_region": cls.ALIBABA_CLOUD_REGION,
            "amap_api_key": "***" if cls.AMAP_API_KEY else None,
            "mcp_server_url": cls.MCP_SERVER_URL,
            "mcp_client_url": cls.MCP_CLIENT_URL,
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG,
        }

# 创建全局配置实例
config = Config()

# 验证配置
if __name__ == "__main__":
    config.validate_config()
    print("配置信息:")
    for key, value in config.get_config_info().items():
        print(f"  {key}: {value}")
