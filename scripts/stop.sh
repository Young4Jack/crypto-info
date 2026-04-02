#!/bin/bash
# Crypto-info 服务停止脚本

# 获取项目目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

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

# 额外清理：通过进程名停止可能残留的进程
pkill -f "python.*run.py" 2>/dev/null && echo "✅ 清理残留后端进程"
pkill -f "python.*proxy.py" 2>/dev/null && echo "✅ 清理残留代理进程"

echo ""
echo "所有服务已停止"
