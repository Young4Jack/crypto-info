# 多阶段构建 - 前端构建阶段
# 修复 1 & 2: 
#   1. 升级 Node 到 22 (满足 Vite 要求的 22.12+ / 20.19+)，解决版本过低警告
#   2. 从 alpine (musl) 切换到 slim (glibc) 以修复在 buildx 跨架构构建时，
#      Vite 打包器 rolldown 找不到 linux-arm64-musl 绑定的崩溃问题。
FROM node:22-slim AS frontend-build

WORKDIR /frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
# 修复 3: 在 multi-platform 构建中，不使用 npm ci，因为 package-lock.json 
# 通常是在本地 (amd64) 生成的。使用 npm install 可以让 npm 在
# 容器内 (无论是 arm64 还是 amd64) 重新解析并拉取该架构所需的二进制依赖。
RUN npm install

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

# 创建非 root 用户 (如果需要，取消注释并修改权限)
# RUN useradd --create-home --shell /bin/bash app \
#     && chown -R app:app /app
# USER app

# 暴露端口（可通过环境变量覆盖）
ENV BACKEND_PORT=8000
ENV FRONTEND_PORT=5173
EXPOSE $BACKEND_PORT $FRONTEND_PORT

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$BACKEND_PORT/health || exit 1

# 启动脚本
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]