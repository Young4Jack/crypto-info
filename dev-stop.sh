#!/bin/bash
# Crypto-info 本地停止脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "正在停止 Crypto-info 服务..."

# 通过 PID 文件停止
if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo "✅ 已停止后端服务 (PID: $PID)"
    fi
    rm -f .backend.pid
fi

if [ -f ".proxy.pid" ]; then
    PID=$(cat .proxy.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
        echo "✅ 已停止代理服务 (PID: $PID)"
    fi
    rm -f .proxy.pid
fi

# 清理可能残留的进程
pkill -f "python.*run.py" 2>/dev/null
pkill -f "python.*proxy.py" 2>/dev/null

echo "所有服务已停止"
