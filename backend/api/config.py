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
from services.config_manager import ConfigManager

logger = get_logger(__name__)
router = APIRouter()

# Pydantic 模型定义
class ScanConfig(BaseModel):
    """扫描配置"""
    directory: str = Field(..., description="扫描目录路径")
    target_formats: List[str] = Field(default=["mp4", "mkv"], description="目标视频格式")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")
    dry_run: bool = Field(default=False, description="是否仅预览不执行")
    custom_video_extensions: List[str] = Field(default=[], description="自定义视频扩展名")
    custom_metadata_extensions: List[str] = Field(default=[], description="自定义元数据扩展名")

class CreateScanConfig(BaseModel):
    """创建扫描配置"""
    name: str = Field(..., description="配置名称")
    description: str = Field(default="", description="配置描述")
    directory: str = Field(..., description="扫描目录路径")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")
    custom_video_extensions: List[str] = Field(default=[], description="自定义视频扩展名")
    custom_metadata_extensions: List[str] = Field(default=[], description="自定义元数据扩展名")

class SavedScanConfig(BaseModel):
    """保存的扫描配置"""
    config_id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    description: str = Field(default="", description="配置描述")
    directory: str = Field(..., description="扫描目录路径")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")
    custom_video_extensions: List[str] = Field(default=[], description="自定义视频扩展名")
    custom_metadata_extensions: List[str] = Field(default=[], description="自定义元数据扩展名")
    created_at: str = Field(default="", description="创建时间")
    updated_at: str = Field(default="", description="更新时间")

class ScanConfigUpdate(BaseModel):
    """扫描配置更新"""
    name: Optional[str] = Field(None, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    directory: Optional[str] = Field(None, description="扫描目录路径")
    recursive: Optional[bool] = Field(None, description="是否递归扫描子目录")
    custom_video_extensions: Optional[List[str]] = Field(None, description="自定义视频扩展名")
    custom_metadata_extensions: Optional[List[str]] = Field(None, description="自定义元数据扩展名")

class ScanResult(BaseModel):
    """扫描结果"""
    success: bool
    directory: str
    total_files: int
    processed: int
    created_links: int
    skipped: int
    errors: List[Dict]
    details: List[Dict]
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
    scan_config_id: Optional[str] = Field(None, description="关联的扫描配置ID")
    custom_video_extensions: List[str] = Field(default=[], description="自定义视频扩展名")
    custom_metadata_extensions: List[str] = Field(default=[], description="自定义元数据扩展名")

class ExtensionConfig(BaseModel):
    """扩展名配置"""
    video_extensions: List[str] = Field(default=[], description="自定义视频扩展名")
    metadata_extensions: List[str] = Field(default=[], description="自定义元数据扩展名")

# 全局服务实例（将在 main.py 中注入）
scanner = StrmScanner()
config_manager = ConfigManager()
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
        
        # 创建临时扫描器实例，应用自定义扩展名
        temp_scanner = StrmScanner(
            custom_video_extensions=config.custom_video_extensions,
            custom_metadata_extensions=config.custom_metadata_extensions
        )
        
        # 执行扫描
        result = temp_scanner.scan_directory(
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
    global scheduler_service, config_manager
    
    if not scheduler_service:
        raise HTTPException(status_code=500, detail="调度服务未初始化")
    
    # 如果指定了扫描配置ID，验证配置是否存在
    scan_config = None
    if config.scan_config_id:
        scan_config = config_manager.get_config(config.scan_config_id)
        if not scan_config:
            raise HTTPException(status_code=400, detail=f"扫描配置不存在: {config.scan_config_id}")
    
    # 使用扫描配置或直接参数
    if scan_config:
        # 使用保存的扫描配置
        success = scheduler_service.add_scan_task(
            task_id=config.task_id,
            directory=scan_config["directory"],
            target_formats=config.target_formats,
            schedule_type=config.schedule_type,
            schedule_params=config.schedule_params,
            enabled=config.enabled,
            recursive=scan_config.get("recursive", True),
            custom_video_extensions=scan_config.get("custom_video_extensions", []),
            custom_metadata_extensions=scan_config.get("custom_metadata_extensions", [])
        )
    else:
        # 使用直接参数
        success = scheduler_service.add_scan_task(
            task_id=config.task_id,
            directory=config.directory,
            target_formats=config.target_formats,
            schedule_type=config.schedule_type,
            schedule_params=config.schedule_params,
            enabled=config.enabled,
            recursive=config.recursive,
            custom_video_extensions=config.custom_video_extensions,
            custom_metadata_extensions=config.custom_metadata_extensions
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

# 扩展名管理相关接口
@router.get("/extensions")
async def get_supported_extensions():
    """获取支持的扩展名列表"""
    global scanner
    
    extensions = scanner.get_supported_extensions()
    return {
        "video_extensions": sorted(list(extensions["video_extensions"])),
        "metadata_extensions": sorted(list(extensions["metadata_extensions"]))
    }

@router.post("/extensions/video")
async def add_video_extension(extension: str):
    """添加自定义视频扩展名"""
    global scanner
    
    try:
        scanner.add_video_extension(extension)
        return {"message": f"成功添加视频扩展名: {extension}"}
    except Exception as e:
        logger.error(f"添加视频扩展名失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/extensions/metadata")
async def add_metadata_extension(extension: str):
    """添加自定义元数据扩展名"""
    global scanner
    
    try:
        scanner.add_metadata_extension(extension)
        return {"message": f"成功添加元数据扩展名: {extension}"}
    except Exception as e:
        logger.error(f"添加元数据扩展名失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/extensions/batch")
async def add_extensions_batch(config: ExtensionConfig):
    """批量添加扩展名"""
    global scanner
    
    try:
        results = {
            "video_extensions": [],
            "metadata_extensions": []
        }
        
        for ext in config.video_extensions:
            scanner.add_video_extension(ext)
            results["video_extensions"].append(ext)
        
        for ext in config.metadata_extensions:
            scanner.add_metadata_extension(ext)
            results["metadata_extensions"].append(ext)
        
        return {
            "message": "批量添加扩展名成功",
            "added": results
        }
    except Exception as e:
        logger.error(f"批量添加扩展名失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# 扫描配置管理相关接口
@router.get("/scan-configs")
async def get_scan_configs():
    """获取所有扫描配置"""
    global config_manager
    
    configs = config_manager.get_all_configs()
    return {"configs": configs}

@router.get("/scan-configs/{config_id}")
async def get_scan_config(config_id: str):
    """获取指定扫描配置"""
    global config_manager
    
    config = config_manager.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
    
    return config

@router.post("/scan-configs")
async def create_scan_config(config_data: CreateScanConfig):
    """创建新的扫描配置"""
    global config_manager
    
    # 验证配置数据
    errors = config_manager.validate_config(config_data.dict())
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # 检查名称是否已存在
    existing_config = config_manager.get_config_by_name(config_data.name)
    if existing_config:
        raise HTTPException(status_code=400, detail=f"配置名称已存在: {config_data.name}")
    
    # 创建配置
    config_id = config_manager.create_config(config_data.dict())
    
    return {
        "message": "扫描配置创建成功",
        "config_id": config_id
    }

@router.put("/scan-configs/{config_id}")
async def update_scan_config(config_id: str, config_data: ScanConfigUpdate):
    """更新扫描配置"""
    global config_manager
    
    # 检查配置是否存在
    existing_config = config_manager.get_config(config_id)
    if not existing_config:
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
    
    # 验证配置数据
    update_data = {k: v for k, v in config_data.dict().items() if v is not None}
    if update_data:
        errors = config_manager.validate_config(update_data)
        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # 检查名称是否与其他配置冲突
        if "name" in update_data:
            existing_config_with_name = config_manager.get_config_by_name(update_data["name"])
            if existing_config_with_name and existing_config_with_name["config_id"] != config_id:
                raise HTTPException(status_code=400, detail=f"配置名称已存在: {update_data['name']}")
        
        # 更新配置
        success = config_manager.update_config(config_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新配置失败")
    
    return {"message": "扫描配置更新成功"}

@router.delete("/scan-configs/{config_id}")
async def delete_scan_config(config_id: str):
    """删除扫描配置"""
    global config_manager
    
    success = config_manager.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
    
    return {"message": "扫描配置删除成功"}

@router.post("/scan-configs/{config_id}/execute")
async def execute_scan_config(config_id: str, dry_run: bool = False):
    """执行指定的扫描配置"""
    global config_manager
    
    # 获取配置
    config = config_manager.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_id}")
    
    try:
        # 验证目录
        directory_path = Path(config["directory"])
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail=f"目录不存在: {config['directory']}")
        
        if not directory_path.is_dir():
            raise HTTPException(status_code=400, detail=f"路径不是目录: {config['directory']}")
        
        logger.info(f"执行扫描配置: {config['name']} (ID: {config_id})")
        
        # 创建扫描器实例，应用自定义扩展名
        temp_scanner = StrmScanner(
            custom_video_extensions=config.get("custom_video_extensions", []),
            custom_metadata_extensions=config.get("custom_metadata_extensions", [])
        )
        
        # 执行扫描
        result = temp_scanner.scan_directory(
            directory=config["directory"],
            recursive=config.get("recursive", True),
            dry_run=dry_run
        )
        
        return ScanResult(**result)
        
    except Exception as e:
        logger.error(f"执行扫描配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 服务注入函数（在 main.py 中调用）
def set_services(watcher: WatcherService, scheduler: SchedulerService):
    """注入服务实例"""
    global watcher_service, scheduler_service
    watcher_service = watcher
    scheduler_service = scheduler
