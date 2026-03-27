#!/usr/bin/env python3
"""后端服务启动脚本"""
import uvicorn
import socket
import sys
from app.config import settings

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
    # 获取本机IP
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🚀 Crypto-info 后端服务启动中...")
    print("=" * 60)
    print(f"📍 本地访问: http://localhost:8000")
    print(f"📍 局域网访问: http://{local_ip}:8000")
    print(f"📚 API文档: http://localhost:8000/docs")
    print(f"📚 局域网文档: http://{local_ip}:8000/docs")
    print("=" * 60)
    print("💡 提示: 确保防火墙允许8000端口访问")
    print("💡 提示: 前端需要配置正确的API地址")
    print("=" * 60)
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
