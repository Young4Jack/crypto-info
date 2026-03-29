#!/bin/bash
set -e

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo "初始化数据目录与软链接..."
mkdir -p /app/data
ln -sf /app/data/config.json /app/config.json

# 给数据库文件也做软链接
ln -sf /app/data/crypto.db /app/backend/crypto.db

echo "生成 Nginx 反向代理配置..."
# 利用 cat 写入完整的 Nginx 配置
cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen $FRONTEND_PORT;
    server_name localhost;

    # 1. 拦截所有 /api 开头的请求，转发给本地的后端进程
    location /api/ {
        # 注意 8000 后面的斜杠 / 极其重要，它会将 /api 前缀抹除后再转发给后端
        proxy_pass http://127.0.0.1:$BACKEND_PORT/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 2. 其他所有请求，都视为前端静态文件请求
    location / {
        root /app/frontend;
        index index.html;
        # 兼容 Vue Router 的 History 模式
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

echo "启动 Nginx..."
nginx

sleep 2

# 1. 将 backend 目录强行加入 Python 的模块搜索路径
export PYTHONPATH=/app/backend

echo "执行数据库表结构迁移..."
cd backend
alembic upgrade head
cd ..

echo "检查并初始化数据库默认数据..."
# 2. 此时 Python 已经认识 app 模块了，直接以模块形式运行
python -m app.init_db

echo "启动后端服务..."
exec uvicorn backend.app.main:app --host 127.0.0.1 --port $BACKEND_PORT