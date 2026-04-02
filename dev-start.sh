#!/bin/bash
# Crypto-info 本地启动脚本（使用代理服务器模式）

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查前端是否已编译
if [ ! -d "frontend/dist" ]; then
    echo "❌ 前端未编译，请先运行: cd frontend && npm run build"
    exit 1
fi

# 读取端口配置
BACKEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))" 2>/dev/null || echo "8000")
FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))" 2>/dev/null || echo "5173")

# 检查是否已经在运行
if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  后端服务已在运行 (PID: $PID)"
        exit 1
    fi
fi

if [ -f ".proxy.pid" ]; then
    PID=$(cat .proxy.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  代理服务已在运行 (PID: $PID)"
        exit 1
    fi
fi

# 启动后端
echo "🚀 启动后端服务..."
cd backend
source venv/bin/activate
nohup python run.py > /dev/null 2>&1 &
BACKEND_PID=$!
cd ..
echo $BACKEND_PID > .backend.pid
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动代理
echo "🚀 启动代理服务..."
cd scripts
nohup python3 proxy.py > /dev/null 2>&1 &
PROXY_PID=$!
cd ..
echo $PROXY_PID > .proxy.pid
echo "   代理 PID: $PROXY_PID"

# 获取本机IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
else
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
fi

echo ""
echo "============================================================"
echo "        ✅ Crypto-info 启动成功！"
echo "============================================================"
echo ""
echo "📍 本地访问: http://localhost:$FRONTEND_PORT"
echo "📍 局域网访问: http://$LOCAL_IP:$FRONTEND_PORT"
echo "📚 API文档: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "停止服务: ./dev-stop.sh"
echo "============================================================"
