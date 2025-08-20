@echo off
REM STRM Linker Windows 启动脚本

echo 🚀 启动 STRM Linker 后端服务...

REM 检查是否在虚拟环境中
if defined VIRTUAL_ENV (
    echo ✅ 检测到虚拟环境: %VIRTUAL_ENV%
) else (
    echo ⚠️  未检测到虚拟环境，建议使用虚拟环境运行
    echo.
    echo 创建虚拟环境的步骤:
    echo 1. python -m venv venv
    echo 2. venv\Scripts\activate
    echo 3. pip install -r requirements.txt
    echo 4. run.bat
    echo.
    set /p continue="是否继续运行? (y/N): "
    if /i not "%continue%"=="y" exit /b 0
)

REM 检查 Python 和依赖
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或未在 PATH 中
    exit /b 1
)

REM 设置环境变量
set PYTHONPATH=%~dp0
set APP_HOST=0.0.0.0
set APP_PORT=8000

REM 启动应用
echo 📍 访问地址: http://localhost:8000
echo 📚 API 文档: http://localhost:8000/api/docs
echo.

python run.py

pause
