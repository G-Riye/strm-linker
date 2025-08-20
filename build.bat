@echo off
REM STRM Linker Windows 构建和部署脚本
setlocal enabledelayedexpansion

REM 颜色定义（使用 echo 命令的特殊字符）
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 打印带颜色的消息函数模拟
call :print_message "🚀 STRM Linker Windows 构建脚本" "BLUE"

REM 检查 Docker 和 Docker Compose
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_message "❌ Docker 未安装或未启动，请先安装 Docker Desktop" "RED"
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_message "❌ Docker Compose 未安装，请先安装 Docker Compose" "RED"
    exit /b 1
)

REM 默认操作
set "ACTION=%1"
if "%ACTION%"=="" set "ACTION=build"

goto %ACTION% 2>nul || goto help

:build
    call :print_message "🔨 构建 Docker 镜像..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose build
    if %errorlevel% equ 0 (
        call :print_message "✅ 镜像构建完成" "GREEN"
    ) else (
        call :print_message "❌ 镜像构建失败" "RED"
        exit /b 1
    )
    goto :eof

:start
    call :print_message "🚀 启动服务..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose up -d
    if %errorlevel% equ 0 (
        call :print_message "✅ 服务启动成功" "GREEN"
        call :print_message "📍 访问地址: http://localhost:8080" "BLUE"
    ) else (
        call :print_message "❌ 服务启动失败" "RED"
        exit /b 1
    )
    goto :eof

:stop
    call :print_message "⏹️ 停止服务..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose down
    if %errorlevel% equ 0 (
        call :print_message "✅ 服务已停止" "GREEN"
    )
    goto :eof

:restart
    call :print_message "🔄 重启服务..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose down
    docker-compose up -d
    if %errorlevel% equ 0 (
        call :print_message "✅ 服务重启成功" "GREEN"
        call :print_message "📍 访问地址: http://localhost:8080" "BLUE"
    )
    goto :eof

:logs
    call :print_message "📋 查看服务日志..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose logs -f
    goto :eof

:clean
    call :print_message "🧹 清理 Docker 资源..." "YELLOW"
    cd /d "%~dp0\docker"
    docker-compose down -v --remove-orphans
    docker system prune -f
    call :print_message "✅ 清理完成" "GREEN"
    goto :eof

:dev
    call :print_message "🛠️ 开发模式启动..." "YELLOW"
    call :print_message "❌ Windows 开发模式请使用以下命令手动启动：" "RED"
    echo.
    echo 后端服务：
    echo cd backend
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install -r requirements.txt
    echo run.bat
    echo.
    echo 前端服务：
    echo cd frontend
    echo npm install
    echo npm run dev
    echo.
    call :print_message "📍 前端地址: http://localhost:3000" "BLUE"
    call :print_message "📍 后端地址: http://localhost:8000" "BLUE"
    goto :eof

:test
    call :print_message "🧪 运行测试..." "YELLOW"
    
    REM 测试后端
    if exist "backend\requirements.txt" (
        cd /d "%~dp0\backend"
        python -c "import sys; sys.path.insert(0, '.'); from main import app; print('✅ 后端应用检查通过')" 2>nul
        if %errorlevel% neq 0 (
            call :print_message "❌ 后端应用检查失败" "RED"
            cd /d "%~dp0"
            goto :eof
        )
        cd /d "%~dp0"
    )
    
    REM 测试前端构建
    if exist "frontend\package.json" (
        cd /d "%~dp0\frontend"
        if not exist "node_modules" (
            call :print_message "正在安装前端依赖..." "YELLOW"
            npm install
        )
        npm run build
        if exist "dist\index.html" (
            call :print_message "✅ 前端构建测试通过" "GREEN"
        ) else (
            call :print_message "❌ 前端构建测试失败" "RED"
            cd /d "%~dp0"
            goto :eof
        )
        cd /d "%~dp0"
    )
    
    call :print_message "✅ 所有测试通过" "GREEN"
    goto :eof

:admin-check
    call :print_message "🔍 检查管理员权限..." "YELLOW"
    
    REM 检查是否以管理员身份运行
    net session >nul 2>&1
    if %errorlevel% equ 0 (
        call :print_message "✅ 当前以管理员身份运行" "GREEN"
        call :print_message "💡 可以创建符号链接以获得最佳性能" "BLUE"
    ) else (
        call :print_message "⚠️ 当前非管理员身份运行" "YELLOW"
        call :print_message "💡 建议以管理员身份重新运行以创建符号链接" "YELLOW"
        call :print_message "💡 或启用 Windows 开发者模式允许非管理员创建符号链接" "YELLOW"
    )
    goto :eof

:help
    call :print_message "📖 Windows 使用说明:" "BLUE"
    echo.
    echo   %~n0 [命令]
    echo.
    echo 可用命令:
    echo   build       - 构建 Docker 镜像
    echo   start       - 启动服务
    echo   stop        - 停止服务
    echo   restart     - 重启服务
    echo   logs        - 查看日志
    echo   clean       - 清理 Docker 资源
    echo   dev         - 开发模式说明
    echo   test        - 运行测试
    echo   admin-check - 检查管理员权限
    echo   help        - 显示此帮助信息
    echo.
    call :print_message "💡 Windows 特别说明:" "YELLOW"
    echo   - 建议以管理员权限运行以获得最佳性能
    echo   - 或启用开发者模式允许创建符号链接
    echo   - 确保已安装并启动 Docker Desktop
    echo.
    call :print_message "示例:" "YELLOW"
    echo   %~n0 build
    echo   %~n0 start
    echo   %~n0 admin-check
    goto :eof

REM 打印消息函数
:print_message
    set "msg=%~1"
    set "color=%~2"
    
    REM 移除颜色，在 Windows 批处理中简化输出
    echo %msg%
    goto :eof

:eof
