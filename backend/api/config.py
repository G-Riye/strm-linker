"""
配置管理 API
处理扫描配置、任务管理等
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path

from services.logger import get_logger
from services.scanner import StrmScanner
from services.watcher import WatcherService
from services.scheduler import SchedulerService

logger = get_logger(__name__)
router = APIRouter()

# Pydantic 模型定义
class ScanConfig(BaseModel):
    """扫描配置"""
    directory: str = Field(..., description="扫描目录路径")
    target_formats: List[str] = Field(default=["mp4", "mkv"], description="目标视频格式")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")
    dry_run: bool = Field(default=False, description="是否仅预览不执行")

class ScanResult(BaseModel):
    """扫描结果"""
    success: bool
    directory: str
    total_files: int
    processed: int
    created_links: int
    skipped: int
    errors: List[Dict]
    duration: float

class WatchConfig(BaseModel):
    """监听配置"""
    directory: str = Field(..., description="监听目录路径")
    target_formats: List[str] = Field(default=["mp4", "mkv"], description="目标视频格式")
    recursive: bool = Field(default=True, description="是否递归监听子目录")

class ScheduleConfig(BaseModel):
    """定时任务配置"""
    task_id: str = Field(..., description="任务ID")
    directory: str = Field(..., description="扫描目录")
    target_formats: List[str] = Field(default=["mp4", "mkv"], description="目标格式")
    schedule_type: str = Field(..., description="调度类型: cron 或 interval")
    schedule_params: Dict[str, Any] = Field(..., description="调度参数")
    enabled: bool = Field(default=True, description="是否启用")
    recursive: bool = Field(default=True, description="是否递归")

# 全局服务实例（将在 main.py 中注入）
scanner = StrmScanner()
watcher_service = None
scheduler_service = None

@router.post("/scan", response_model=ScanResult)
async def scan_directory(config: ScanConfig, background_tasks: BackgroundTasks):
    """执行目录扫描"""
    try:
        # 验证目录
        directory_path = Path(config.directory)
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail=f"目录不存在: {config.directory}")
        
        if not directory_path.is_dir():
            raise HTTPException(status_code=400, detail=f"路径不是目录: {config.directory}")
        
        logger.info(f"开始扫描目录: {config.directory}")
        
        # 执行扫描
        result = scanner.scan_directory(
            directory=config.directory,
            target_formats=config.target_formats,
            recursive=config.recursive,
            dry_run=config.dry_run
        )
        
        return ScanResult(**result)
        
    except Exception as e:
        logger.error(f"扫描目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_broken_links(directory: str, recursive: bool = True):
    """清理损坏的软链接"""
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")
        
        result = scanner.cleanup_broken_links(directory, recursive)
        return result
        
    except Exception as e:
        logger.error(f"清理软链接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 文件监听相关接口
@router.get("/watch/status")
async def get_watch_status():
    """获取文件监听状态"""
    global watcher_service
    
    if not watcher_service:
        return {"is_running": False, "watch_directories": []}
    
    return watcher_service.get_watch_status()

@router.post("/watch/start")
async def start_watcher():
    """启动文件监听服务"""
    global watcher_service
    
    if not watcher_service:
        raise HTTPException(status_code=500, detail="监听服务未初始化")
    
    success = watcher_service.start()
    if success:
        return {"message": "文件监听服务启动成功"}
    else:
        raise HTTPException(status_code=500, detail="启动文件监听服务失败")

@router.post("/watch/stop")
async def stop_watcher():
    """停止文件监听服务"""
    global watcher_service
    
    if not watcher_service:
        raise HTTPException(status_code=500, detail="监听服务未初始化")
    
    success = watcher_service.stop()
    if success:
        return {"message": "文件监听服务停止成功"}
    else:
        raise HTTPException(status_code=500, detail="停止文件监听服务失败")

@router.post("/watch/add")
async def add_watch_directory(config: WatchConfig):
    """添加监听目录"""
    global watcher_service
    
    if not watcher_service:
        raise HTTPException(status_code=500, detail="监听服务未初始化")
    
    success = watcher_service.add_watch_directory(
        directory=config.directory,
        target_formats=config.target_formats,
        recursive=config.recursive
    )
    
    if success:
        return {"message": f"成功添加监听目录: {config.directory}"}
    else:
        raise HTTPException(status_code=400, detail=f"添加监听目录失败: {config.directory}")

@router.delete("/watch/remove")
async def remove_watch_directory(directory: str):
    """移除监听目录"""
    global watcher_service
    
    if not watcher_service:
        raise HTTPException(status_code=500, detail="监听服务未初始化")
    
    success = watcher_service.remove_watch_directory(directory)
    
    if success:
        return {"message": f"成功移除监听目录: {directory}"}
    else:
        raise HTTPException(status_code=400, detail=f"移除监听目录失败: {directory}")

# 定时任务相关接口
@router.get("/schedule/tasks")
async def get_scheduled_tasks():
    """获取所有定时任务"""
    global scheduler_service
    
    if not scheduler_service:
        return []
    
    return scheduler_service.get_tasks()

@router.post("/schedule/add")
async def add_scheduled_task(config: ScheduleConfig):
    """添加定时任务"""
    global scheduler_service
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    success = scheduler_service.add_scan_task(
        task_id=config.task_id,
        directory=config.directory,
        target_formats=config.target_formats,
        schedule_type=config.schedule_type,
        schedule_params=config.schedule_params,
        enabled=config.enabled,
        recursive=config.recursive
    )
    
    if success:
        return {"message": f"成功添加定时任务: {config.task_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"添加定时任务失败: {config.task_id}")

@router.delete("/schedule/remove/{task_id}")
async def remove_scheduled_task(task_id: str):
    """删除定时任务"""
    global scheduler_service
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    success = scheduler_service.remove_task(task_id)
    
    if success:
        return {"message": f"成功删除定时任务: {task_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"删除定时任务失败: {task_id}")

@router.post("/schedule/enable/{task_id}")
async def enable_scheduled_task(task_id: str):
    """启用定时任务"""
    global scheduler_service
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    success = scheduler_service.enable_task(task_id)
    
    if success:
        return {"message": f"成功启用定时任务: {task_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"启用定时任务失败: {task_id}")

@router.post("/schedule/disable/{task_id}")
async def disable_scheduled_task(task_id: str):
    """禁用定时任务"""
    global scheduler_service
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    success = scheduler_service.disable_task(task_id)
    
    if success:
        return {"message": f"成功禁用定时任务: {task_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"禁用定时任务失败: {task_id}")

@router.post("/schedule/run/{task_id}")
async def run_task_now(task_id: str):
    """立即执行指定任务"""
    global scheduler_service
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    success = scheduler_service.run_task_now(task_id)
    
    if success:
        return {"message": f"成功触发任务执行: {task_id}"}
    else:
        raise HTTPException(status_code=400, detail=f"触发任务执行失败: {task_id}")

@router.get("/schedule/status")
async def get_scheduler_status():
    """获取调度器状态"""
    global scheduler_service
    
    if not scheduler_service:
        return {"is_running": False}
    
    return {"is_running": scheduler_service.is_running()}

# 服务注入函数（在 main.py 中调用）
def set_services(watcher: WatcherService, scheduler: SchedulerService):
    """注入服务实例"""
    global watcher_service, scheduler_service
    watcher_service = watcher
    scheduler_service = scheduler
