#!/bin/bash
set -e

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo "初始化数据目录与软链接..."
mkdir -p /app/data
ln -sf /app/data/config.json /app/config.json

# 给数据库文件也做软链接
ln -sf /app/data/crypto.db /app/backend/crypto.db

echo "生成 Nginx 配置..."
cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen $FRONTEND_PORT;
    server_name _;

    # 1. API 请求转发给后端 (8000)
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # --- WebSocket 支持 ---
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 2. 其他请求服务前端静态文件
    location / {
        root /app/frontend;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

echo "启动 Nginx..."
nginx

sleep 2

echo "执行数据库表结构迁移..."
cd backend
alembic upgrade head
cd ..

echo "检查并初始化数据库默认数据..."
export PYTHONPATH=/app/backend
python -m app.init_db

echo "启动后端服务..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port $BACKEND_PORT
