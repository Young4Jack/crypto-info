#!/usr/bin/env python3
"""后端服务启动脚本"""
import uvicorn
import socket
import sys
from app.config import settings
from app.config_manager import config_manager  # 引入配置管理器

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 创建一个临时socket来获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到一个外部地址（不需要真正连接）
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        return "127.0.0.1"

def main():
    """主函数"""
    local_ip = get_local_ip()
    
    # 获取系统配置中的后端端口，如果没有则默认回退到 8000
    system_settings = config_manager.get_system_settings()
    backend_port = system_settings.get("backend_port", 8000)
    
    print("=" * 60)
    print("🚀 Crypto-info 后端服务启动中...")
    print("=" * 60)
    print(f"📍 本地访问: http://localhost:{backend_port}")
    print(f"📍 局域网访问: http://{local_ip}:{backend_port}")
    print(f"📚 API文档: http://localhost:{backend_port}/docs")
    print(f"📚 局域网文档: http://{local_ip}:{backend_port}/docs")
    print("=" * 60)
    print(f"💡 提示: 确保防火墙允许{backend_port}端口访问")
    print("💡 提示: 前端需要配置正确的API地址")
    print("=" * 60)
    
    # 启动服务器，使用动态端口
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=backend_port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
