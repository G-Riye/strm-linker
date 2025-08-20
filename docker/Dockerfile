# 多阶段构建 Dockerfile - 优化版本
# 阶段1: 前端构建
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# 复制依赖文件（利用 Docker 缓存）
COPY frontend/package*.json ./

# 安装依赖（只安装生产依赖以减少体积）
RUN npm ci --only=production

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build

# 清理 node_modules 减少体积
RUN rm -rf node_modules

# 阶段2: Python 依赖构建
FROM python:3.11-slim as python-builder

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY backend/requirements.txt /tmp/
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# 阶段3: 最终运行镜像
FROM python:3.11-slim

LABEL maintainer="strm-linker"
LABEL description="Emby/Jellyfin STRM file symlink management tool"
LABEL version="1.0.0"

# 安装运行时依赖（最小化安装）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用用户
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# 创建目录结构
RUN mkdir -p \
    /app/backend \
    /app/frontend/dist \
    /app/data/logs \
    /var/log/strm_linker \
    /var/run/nginx \
    /etc/supervisor/conf.d

# 复制 Python 依赖（从构建阶段）
COPY --from=python-builder /root/.local /usr/local

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 复制后端代码
COPY backend/ /app/backend/

# 复制配置文件
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/strm-linker.conf
COPY docker/docker-entrypoint.sh /usr/local/bin/

# 删除默认的 nginx 站点配置
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# 设置权限
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown -R app:app /app && \
    chown -R www-data:www-data /var/lib/nginx /var/log/nginx /var/run/nginx

# 创建数据目录并设置权限
RUN chown -R app:app /app/data /var/log/strm_linker

# 暴露端口
EXPOSE 80

# 设置环境变量
ENV PYTHONPATH="/app/backend" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# 切换到工作目录
WORKDIR /app

# 启动脚本
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
