# 多阶段构建 - 前端构建阶段
FROM node:20-alpine3.18 AS frontend-build

WORKDIR /frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 多阶段构建 - 后端构建阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        nginx \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt ./backend/

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 从前端构建阶段复制构建好的前端文件
COPY --from=frontend-build /frontend/dist /app/frontend

# 复制 nginx 配置
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口（可通过环境变量覆盖）
ENV BACKEND_PORT=8000
ENV FRONTEND_PORT=5173
EXPOSE $BACKEND_PORT $FRONTEND_PORT

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$BACKEND_PORT/health || exit 1

# 启动脚本
COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]