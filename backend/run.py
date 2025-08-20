#!/usr/bin/env python3
"""
STRM Linker 启动脚本
解决 Windows 和其他平台的导入问题
"""

import os
import sys
from pathlib import Path

# 添加后端目录到 Python 路径
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(backend_dir))

# 导入并运行主应用
if __name__ == "__main__":
    try:
        from main import app
        import uvicorn
        
        # 从环境变量获取配置
        host = os.getenv("APP_HOST", "0.0.0.0")
        port = int(os.getenv("APP_PORT", "8000"))
        
        print(f"🚀 启动 STRM Linker 服务...")
        print(f"📍 访问地址: http://{host}:{port}")
        print(f"📚 API 文档: http://{host}:{port}/api/docs")
        
        # 启动服务
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,  # 生产环境不启用热重载
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖都已正确安装:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
