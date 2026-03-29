#!/bin/bash
set -e

# 从环境变量读取端口配置
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo "启动 Crypto-info 服务..."
echo "后端端口: $BACKEND_PORT"
echo "前端端口: $FRONTEND_PORT"

# 更新nginx配置中的端口
sed -i "s/listen 5173/listen $FRONTEND_PORT/g" /etc/nginx/conf.d/default.conf
sed -i "s/proxy_pass http:\/\/localhost:8000/proxy_pass http:\/\/localhost:$BACKEND_PORT/g" /etc/nginx/conf.d/default.conf

# 启动nginx
echo "启动 Nginx..."
nginx

# 等待nginx启动
sleep 2

# 启动后端服务
echo "启动后端服务..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port $BACKEND_PORT