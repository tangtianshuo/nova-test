"""
配置管理模块
提供环境变量加载和配置验证功能
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """执行引擎配置"""

    # Redis 配置
    redis_url: str = "redis://localhost:6379"
    redis_queue_key: str = "queue:agent_tasks"
    redis_stream_prefix: str = "pubsub:agent_stream:"

    # 数据库配置
    database_url: str = ""

    # Fara-7B 视觉模型 RPC 配置
    fara_api_url: str = "http://localhost:8001/v1/chat/completions"
    fara_api_key: str = "sk-dev-key"
    vision_model_name: str = "fara-7b-vision"

    # S3/MinIO 配置
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin123"
    s3_bucket: str = "nova-test"
    s3_region: str = "us-east-1"

    # 执行引擎配置
    max_steps: int = 10
    hil_confidence_threshold: float = 0.7
    browser_headless: bool = True
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 720

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
