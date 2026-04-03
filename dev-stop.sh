#!/bin/bash
# Crypto-info 本地停止脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "正在停止 Crypto-info 服务..."

# 通过 PID 文件停止（SIGKILL 立即终止）
if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill -9 $PID 2>/dev/null
        echo "✅ 已停止后端服务 (PID: $PID)"
    fi
    rm -f .backend.pid
fi

if [ -f ".proxy.pid" ]; then
    PID=$(cat .proxy.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill -9 $PID 2>/dev/null
        echo "✅ 已停止代理服务 (PID: $PID)"
    fi
    rm -f .proxy.pid
fi

# 强制清理残留进程
pkill -9 -f "python.*run.py" 2>/dev/null
pkill -9 -f "python.*proxy.py" 2>/dev/null

# 释放端口（fuser -k 会 kill 占用端口的进程并清除 TIME_WAIT）
BACKEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))" 2>/dev/null || echo "8000")
FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))" 2>/dev/null || echo "5173")

fuser -k $BACKEND_PORT/tcp 2>/dev/null
fuser -k $FRONTEND_PORT/tcp 2>/dev/null

# 等待端口完全释放
sleep 2

echo "所有服务已停止"
