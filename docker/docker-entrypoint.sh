#!/bin/bash
set -e

# STRM Linker Docker 容器启动脚本

echo "🚀 启动 STRM Linker 容器..."

# 创建必要的目录
mkdir -p /app/data/logs
mkdir -p /app/data/config
mkdir -p /var/run/nginx

# 设置权限
chown -R app:app /app/data
chown -R www-data:www-data /var/run/nginx

# 检查后端代码是否存在
if [ ! -f "/app/backend/main.py" ]; then
    echo "❌ 错误: 后端代码不存在，请检查镜像构建"
    exit 1
fi

# 检查前端文件是否存在
if [ ! -f "/app/frontend/dist/index.html" ]; then
    echo "❌ 错误: 前端构建文件不存在，请检查镜像构建"
    exit 1
fi

# 检查静态资源目录
if [ ! -d "/app/frontend/dist/static" ] && [ ! -d "/app/frontend/dist/assets" ]; then
    echo "⚠️  警告: 静态资源目录不存在，但继续启动..."
    # 创建空的静态资源目录
    mkdir -p /app/frontend/dist/static
    chown -R app:app /app/frontend/dist
fi

# 测试 FastAPI 应用是否可以正常导入
echo "🔍 检查 FastAPI 应用..."
cd /app/backend
python -c "
try:
    from main import app
    print('✅ FastAPI 应用检查通过')
except Exception as e:
    print(f'❌ FastAPI 应用检查失败: {e}')
    exit(1)
" || exit 1

# 测试 nginx 配置
echo "🔍 检查 Nginx 配置..."
nginx -t || {
    echo "❌ Nginx 配置检查失败"
    exit 1
}

echo "✅ Nginx 配置检查通过"

# 显示版本信息
echo "📦 容器信息:"
echo "  - Python 版本: $(python --version)"
echo "  - Nginx 版本: $(nginx -v 2>&1)"
echo "  - 应用目录: /app"
echo "  - 数据目录: /app/data"
echo "  - 日志目录: /var/log/strm_linker"

# 显示环境变量
echo "🔧 环境变量:"
echo "  - PYTHONPATH: ${PYTHONPATH:-未设置}"
echo "  - APP_HOST: ${APP_HOST:-0.0.0.0}"
echo "  - APP_PORT: ${APP_PORT:-8000}"
echo "  - LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo "  - TZ: ${TZ:-未设置}"

# 显示挂载的卷
echo "💾 挂载卷:"
df -h | grep -E "(app|media)" || echo "  - 无特殊挂载点"

# 等待一下让所有输出刷新
sleep 1

echo "🎯 启动服务..."

# 启动 supervisord 来管理所有服务
exec supervisord -c /etc/supervisor/conf.d/strm-linker.conf
