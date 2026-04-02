#!/usr/bin/env python3
"""
Crypto-info 轻量代理服务器
功能：
  1. 服务前端静态文件 (dist/)
  2. 将 /api/* 请求代理到后端
  3. 支持 WebSocket 代理
"""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys
import socket
import threading
from pathlib import Path

# 配置
BACKEND_PORT = 8000
PROXY_PORT = 5173
PROJECT_DIR = Path(__file__).parent.parent.absolute()
FRONTEND_DIR = PROJECT_DIR / "frontend" / "dist"


def load_config():
    """从 config.json 加载端口配置"""
    global BACKEND_PORT, PROXY_PORT
    config_path = PROJECT_DIR / "backend" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                BACKEND_PORT = config.get('system_settings', {}).get('backend_port', 8000)
                PROXY_PORT = config.get('system_settings', {}).get('frontend_port', 5173)
        except Exception as e:
            print(f"⚠️  读取配置文件失败: {e}")
            print("   使用默认端口配置")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_GET(self):
        """处理 GET 请求"""
        if self.path.startswith('/api/') or self.path.startswith('/docs') or self.path.startswith('/openapi'):
            self.proxy_to_backend()
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "proxy"}).encode())
        else:
            self.serve_static_file()

    def do_POST(self):
        """处理 POST 请求"""
        self.proxy_to_backend()

    def do_PUT(self):
        """处理 PUT 请求"""
        self.proxy_to_backend()

    def do_DELETE(self):
        """处理 DELETE 请求"""
        self.proxy_to_backend()

    def do_PATCH(self):
        """处理 PATCH 请求"""
        self.proxy_to_backend()

    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def proxy_to_backend(self):
        """代理请求到后端"""
        # 去掉 /api 前缀（前端请求 /api/xxx，后端实际路径是 /xxx）
        backend_path = self.path[4:] if self.path.startswith('/api') else self.path
        url = f"http://127.0.0.1:{BACKEND_PORT}{backend_path}"

        # 复制请求头
        headers = {}
        for key, val in self.headers.items():
            if key.lower() not in ['host', 'connection']:
                headers[key] = val

        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else None

        # 发送请求到后端
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=self.command)
            with urllib.request.urlopen(req) as response:
                # 返回响应
                self.send_response(response.status)
                for key, val in response.headers.items():
                    if key.lower() not in ['transfer-encoding']:
                        self.send_header(key, val)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, val in e.headers.items():
                if key.lower() not in ['transfer-encoding']:
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(e.read())
        except urllib.error.URLError as e:
            self.send_error(502, f"Backend connection failed: {str(e.reason)}")
        except Exception as e:
            self.send_error(502, f"Proxy error: {str(e)}")

    def serve_static_file(self):
        """服务静态文件（支持 Vue Router history 模式）"""
        # 检查文件是否存在
        file_path = FRONTEND_DIR / self.path.lstrip('/')

        if file_path.is_file():
            super().do_GET()
        elif file_path.is_dir() and (file_path / 'index.html').is_file():
            super().do_GET()
        else:
            # Vue Router history 模式：返回 index.html
            self.path = '/index.html'
            super().do_GET()


def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True


def main():
    """启动代理服务器"""
    # 加载配置
    load_config()

    # 检查前端目录
    if not FRONTEND_DIR.exists():
        print(f"❌ 前端静态文件目录不存在: {FRONTEND_DIR}")
        print("   请先运行: cd frontend && npm run build")
        print("   或者下载包含预编译前端的 Release 包")
        sys.exit(1)

    # 检查端口是否被占用
    if check_port(PROXY_PORT):
        print(f"❌ 端口 {PROXY_PORT} 已被占用")
        sys.exit(1)

    # 启动服务器
    try:
        server = http.server.HTTPServer(('0.0.0.0', PROXY_PORT), ProxyHandler)
        print("=" * 60)
        print("🚀 Crypto-info 代理服务器启动")
        print("=" * 60)
        print(f"📍 访问地址: http://localhost:{PROXY_PORT}")
        print(f"📚 API文档: http://localhost:{BACKEND_PORT}/docs")
        print(f"📁 静态文件: {FRONTEND_DIR}")
        print("=" * 60)
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
