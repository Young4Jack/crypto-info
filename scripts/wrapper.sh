#!/bin/bash
# Crypto-info 服务启动 wrapper
# 用于 systemd/launchd 启动服务

set -e

# 获取项目目录（scripts 的父目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目目录
cd "$PROJECT_DIR"

# 创建必要的目录
mkdir -p backend/logs
mkdir -p data

# 读取端口配置
if [ -f "backend/config.json" ]; then
    BACKEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))")
    FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))")
else
    BACKEND_PORT=8000
    FRONTEND_PORT=5173
fi

echo "============================================================"
echo "        Crypto-info 服务启动"
echo "============================================================"
echo "📁 项目目录: $PROJECT_DIR"
echo "🔌 后端端口: $BACKEND_PORT"
echo "🌐 前端端口: $FRONTEND_PORT"
echo "============================================================"

# 启动后端
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动后端服务..."
cd backend
export PYTHONPATH="$PROJECT_DIR/backend"
nohup python run.py > "$PROJECT_DIR/backend/logs/backend.log" 2>&1 &
BACKEND_PID=$!
cd ..

# 保存后端 PID
echo $BACKEND_PID > "$PROJECT_DIR/.backend.pid"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待后端服务就绪..."
sleep 3

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 后端服务运行正常"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 后端服务启动失败，请查看日志: $PROJECT_DIR/backend/logs/backend.log"
    exit 1
fi

# 启动代理服务器
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动代理服务器..."
cd scripts
nohup python3 proxy.py > "$PROJECT_DIR/backend/logs/proxy.log" 2>&1 &
PROXY_PID=$!
cd ..

# 保存代理 PID
echo $PROXY_PID > "$PROJECT_DIR/.proxy.pid"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 代理服务器已启动 (PID: $PROXY_PID)"

# 检查代理是否启动成功
sleep 2
if ps -p $PROXY_PID > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 代理服务器运行正常"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 代理服务器启动失败，请查看日志: $PROJECT_DIR/backend/logs/proxy.log"
    exit 1
fi

# 获取本机 IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
else
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
fi

echo ""
echo "============================================================"
echo "        ✅ Crypto-info 服务启动成功！"
echo "============================================================"
echo ""
echo "📍 本地访问: http://localhost:$FRONTEND_PORT"
echo "📍 局域网访问: http://$LOCAL_IP:$FRONTEND_PORT"
echo "📚 API文档: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "📋 日志文件:"
echo "   后端: $PROJECT_DIR/backend/logs/backend.log"
echo "   代理: $PROJECT_DIR/backend/logs/proxy.log"
echo ""
echo "============================================================"

# 保持脚本运行（用于 systemd）
# 使用 trap 捕获信号，优雅退出
trap 'echo "收到停止信号，正在关闭服务..."; kill $BACKEND_PID $PROXY_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# 等待子进程
wait
