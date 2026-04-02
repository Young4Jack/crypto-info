"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional
import socket
import os
from pathlib import Path
from app.config_manager import config_manager

def get_local_ip():
    """利用UDP协议向外部DNS地址发起模拟连接，操作系统会自动选择正确的本地网卡，从而获取真实的局域网IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

# 1. 动态读取 config.json 中的前端端口（若无则兜底为 5173）
_system_settings = config_manager.get_system_settings()
_frontend_port = _system_settings.get("frontend_port", 5173)

# 2. 动态获取当前机器的局域网 IP
_local_ip = get_local_ip()

# 3. 组合生成白名单列表
DYNAMIC_CORS = [
    f"http://localhost:{_frontend_port}",
    f"http://127.0.0.1:{_frontend_port}",
    f"http://{_local_ip}:{_frontend_port}"
]

# 获取 backend 目录的绝对路径
_BACKEND_DIR = Path(__file__).parent.parent.absolute()

class Settings(BaseSettings):
    """应用设置"""
    # 数据库配置（使用相对路径，支持任意安装位置）
    DATABASE_URL: str = f"sqlite:///{_BACKEND_DIR}/crypto.db"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crypto-info API"
    
    # CORS 配置 (动态生成：包含localhost与当前局域网IP)
    BACKEND_CORS_ORIGINS: list = DYNAMIC_CORS
    
    # 局域网访问配置
    ALLOW_LAN_ACCESS: bool = True
    
    # 调试配置
    DEBUG: bool = True
    
    # 日志配置（使用绝对路径）
    LOG_FILE_PATH: str = str(_BACKEND_DIR / "logs" / "crypto-info.log")
    LOG_MAX_SIZE: int = 20 * 1024 * 1024  # 20MB
    LOG_BACKUP_COUNT: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
