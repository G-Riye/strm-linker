#!/bin/bash
set -e

echo "🔍 调试模式启动..."

# 检查目录结构
echo "📁 检查目录结构:"
ls -la /app/
ls -la /app/backend/
ls -la /app/frontend/dist/

# 检查 Python 环境
echo "🐍 检查 Python 环境:"
python --version
which python
echo "PYTHONPATH: $PYTHONPATH"

# 检查依赖
echo "📦 检查 Python 依赖:"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import uvicorn; print('Uvicorn:', uvicorn.__version__)"

# 尝试启动 FastAPI
echo "🚀 尝试启动 FastAPI:"
cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
