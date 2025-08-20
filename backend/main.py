"""
STRM Linker - Emby/Jellyfin 字幕软链管理工具
FastAPI 主入口文件
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from api import config, logs, browse
from services.logger import setup_logging
from services.scheduler import SchedulerService
from services.watcher import WatcherService

# 设置日志
logger = setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title="STRM Linker",
    description="Emby/Jellyfin 字幕软链管理工具",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该更严格
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
scheduler_service = None
watcher_service = None

# 注册 API 路由
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])
app.include_router(logs.router, prefix="/api/logs", tags=["日志管理"])
app.include_router(browse.router, prefix="/api/browse", tags=["目录浏览"])

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global scheduler_service, watcher_service
    
    logger.info("启动 STRM Linker 服务...")
    
    # 初始化定时任务服务
    scheduler_service = SchedulerService()
    
    # 初始化文件监听服务
    watcher_service = WatcherService()
    
    # 注入服务到 API 模块
    config.set_services(watcher_service, scheduler_service)
    
    logger.info("服务启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global scheduler_service, watcher_service
    
    logger.info("关闭 STRM Linker 服务...")
    
    if scheduler_service:
        scheduler_service.stop()
    
    if watcher_service:
        watcher_service.stop()
    
    logger.info("服务已关闭")

# 静态文件服务（Vue 前端）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dist / "static")), name="static")
    
    @app.get("/")
    async def read_index():
        """提供前端页面"""
        return FileResponse(str(frontend_dist / "index.html"))
    
    @app.get("/{path:path}")
    async def read_frontend(path: str):
        """前端路由处理（SPA）"""
        file_path = frontend_dist / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # 如果文件不存在，返回 index.html（用于前端路由）
        return FileResponse(str(frontend_dist / "index.html"))
else:
    @app.get("/")
    async def read_root():
        """开发模式下的默认页面"""
        return {
            "message": "STRM Linker API 服务运行中",
            "version": "1.0.0",
            "docs": "/api/docs"
        }

# 健康检查端点
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "scheduler": scheduler_service.get_running_status() if scheduler_service else False,
            "watcher": watcher_service.get_running_status() if watcher_service else False
        }
    }

if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
