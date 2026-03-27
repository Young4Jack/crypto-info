"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用设置"""
    # 数据库配置
    DATABASE_URL: str = "sqlite:////home/jacket/Project/Crypto-info/backend/crypto.db"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto-info API"
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:5173",
        "http://0.0.0.0:3000",
        "http://192.168.31.77:5173",
        "http://192.168.31.77:3000"
    ]
    
    # 局域网访问配置
    ALLOW_LAN_ACCESS: bool = True
    
    # 调试配置
    DEBUG: bool = True
    
    # 日志配置
    LOG_FILE_PATH: str = "./logs/crypto-info.log"
    LOG_MAX_SIZE: int = 20 * 1024 * 1024  # 20MB
    LOG_BACKUP_COUNT: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
