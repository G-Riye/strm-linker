#!/bin/bash

# STRM Linker 构建和部署脚本
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}$1${NC}"
}

print_message "🚀 STRM Linker 构建脚本" "$BLUE"

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    print_message "❌ Docker 未安装，请先安装 Docker" "$RED"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_message "❌ Docker Compose 未安装，请先安装 Docker Compose" "$RED"
    exit 1
fi

# 默认操作
ACTION=${1:-"build"}

case $ACTION in
    "build")
        print_message "🔨 构建 Docker 镜像..." "$YELLOW"
        cd docker
        docker-compose build
        print_message "✅ 镜像构建完成" "$GREEN"
        ;;
        
    "start")
        print_message "🚀 启动服务..." "$YELLOW"
        cd docker
        docker-compose up -d
        print_message "✅ 服务启动成功" "$GREEN"
        print_message "📍 访问地址: http://localhost:8080" "$BLUE"
        ;;
        
    "stop")
        print_message "⏹️  停止服务..." "$YELLOW"
        cd docker
        docker-compose down
        print_message "✅ 服务已停止" "$GREEN"
        ;;
        
    "restart")
        print_message "🔄 重启服务..." "$YELLOW"
        cd docker
        docker-compose down
        docker-compose up -d
        print_message "✅ 服务重启成功" "$GREEN"
        print_message "📍 访问地址: http://localhost:8080" "$BLUE"
        ;;
        
    "logs")
        print_message "📋 查看服务日志..." "$YELLOW"
        cd docker
        docker-compose logs -f
        ;;
        
    "clean")
        print_message "🧹 清理 Docker 资源..." "$YELLOW"
        cd docker
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_message "✅ 清理完成" "$GREEN"
        ;;
        
    "dev")
        print_message "🛠️  开发模式启动..." "$YELLOW"
        
        # 启动后端
        print_message "启动后端服务..." "$BLUE"
        cd backend
        if [ ! -d "venv" ]; then
            python -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
        python main.py &
        BACKEND_PID=$!
        
        # 启动前端
        print_message "启动前端服务..." "$BLUE"
        cd ../frontend
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run dev &
        FRONTEND_PID=$!
        
        print_message "✅ 开发服务启动成功" "$GREEN"
        print_message "📍 前端地址: http://localhost:3000" "$BLUE"
        print_message "📍 后端地址: http://localhost:8000" "$BLUE"
        print_message "按 Ctrl+C 停止服务" "$YELLOW"
        
        # 等待用户中断
        trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
        wait
        ;;
        
    "test")
        print_message "🧪 运行测试..." "$YELLOW"
        
        # 测试后端
        if [ -f "backend/requirements.txt" ]; then
            cd backend
            python -c "
import sys
try:
    from main import app
    print('✅ 后端应用检查通过')
except Exception as e:
    print(f'❌ 后端应用检查失败: {e}')
    sys.exit(1)
"
        fi
        
        # 测试前端构建
        if [ -f "frontend/package.json" ]; then
            cd frontend
            if [ ! -d "node_modules" ]; then
                npm install
            fi
            npm run build
            print_message "✅ 前端构建测试通过" "$GREEN"
        fi
        
        print_message "✅ 所有测试通过" "$GREEN"
        ;;
        
    "help"|*)
        print_message "📖 使用说明:" "$BLUE"
        echo ""
        echo "  ./build.sh [命令]"
        echo ""
        echo "可用命令:"
        echo "  build    - 构建 Docker 镜像"
        echo "  start    - 启动服务"
        echo "  stop     - 停止服务"
        echo "  restart  - 重启服务"
        echo "  logs     - 查看日志"
        echo "  clean    - 清理 Docker 资源"
        echo "  dev      - 开发模式启动"
        echo "  test     - 运行测试"
        echo "  help     - 显示此帮助信息"
        echo ""
        print_message "示例:" "$YELLOW"
        echo "  ./build.sh build && ./build.sh start"
        ;;
esac
