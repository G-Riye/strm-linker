"""
定时任务服务
管理扫描任务的定时执行
"""

import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job

from services.logger import get_logger
from services.scanner import StrmScanner

logger = get_logger(__name__)

class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self):
        self.scheduler = None
        self.scanner = StrmScanner()
        self.is_running = False
        self._lock = threading.Lock()
        self.job_callbacks = []  # 任务执行回调
        
        # 预定义的任务配置
        self.tasks = {}  # task_id -> task_config
    
    def start(self) -> bool:
        """启动调度器"""
        with self._lock:
            if self.is_running:
                logger.warning("调度器已经在运行")
                return True
            
            try:
                self.scheduler = BackgroundScheduler(
                    timezone='Asia/Shanghai',
                    job_defaults={
                        'coalesce': True,  # 合并延迟执行的任务
                        'max_instances': 1  # 每个任务最多只有一个实例运行
                    }
                )
                
                self.scheduler.start()
                self.is_running = True
                
                logger.info("定时任务调度器启动成功")
                return True
                
            except Exception as e:
                logger.error(f"启动调度器失败: {e}")
                self.is_running = False
                return False
    
    def stop(self) -> bool:
        """停止调度器"""
        with self._lock:
            if not self.is_running:
                logger.warning("调度器未在运行")
                return True
            
            try:
                if self.scheduler:
                    self.scheduler.shutdown(wait=True)
                    self.scheduler = None
                
                self.is_running = False
                logger.info("定时任务调度器已停止")
                return True
                
            except Exception as e:
                logger.error(f"停止调度器失败: {e}")
                return False
    
    def add_scan_task(
        self,
        task_id: str,
        directory: str,
        target_formats: List[str],
        schedule_type: str,  # 'cron' or 'interval'
        schedule_params: Dict,
        enabled: bool = True,
        recursive: bool = True
    ) -> bool:
        """
        添加扫描任务
        
        Args:
            task_id: 任务唯一标识
            directory: 扫描目录
            target_formats: 目标视频格式
            schedule_type: 调度类型 ('cron' 或 'interval')
            schedule_params: 调度参数
                - cron: {'hour': 3, 'minute': 0} 每天3点执行
                - interval: {'hours': 6} 每6小时执行一次
            enabled: 是否启用任务
            recursive: 是否递归扫描
        """
        if not self.is_running or not self.scheduler:
            logger.error("调度器未运行，无法添加任务")
            return False
        
        try:
            # 移除已存在的任务
            if task_id in self.tasks:
                self.remove_task(task_id)
            
            # 创建触发器
            if schedule_type == 'cron':
                trigger = CronTrigger(**schedule_params)
            elif schedule_type == 'interval':
                trigger = IntervalTrigger(**schedule_params)
            else:
                raise ValueError(f"不支持的调度类型: {schedule_type}")
            
            # 任务配置
            task_config = {
                "task_id": task_id,
                "directory": directory,
                "target_formats": target_formats,
                "schedule_type": schedule_type,
                "schedule_params": schedule_params,
                "recursive": recursive,
                "enabled": enabled,
                "created_at": datetime.now(),
                "last_run": None,
                "run_count": 0
            }
            
            # 添加任务
            if enabled:
                job = self.scheduler.add_job(
                    func=self._execute_scan_task,
                    trigger=trigger,
                    args=[task_id],
                    id=task_id,
                    name=f"STRM扫描任务: {directory}",
                    replace_existing=True
                )
                task_config["job"] = job
            
            self.tasks[task_id] = task_config
            
            logger.info(f"添加定时扫描任务: {task_id} -> {directory} ({schedule_type})")
            return True
            
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        try:
            # 从调度器中移除
            if self.scheduler and self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
            
            # 从任务列表中移除
            del self.tasks[task_id]
            
            logger.info(f"移除定时任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除任务失败: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task_config = self.tasks[task_id]
        
        if task_config["enabled"]:
            logger.warning(f"任务已启用: {task_id}")
            return True
        
        try:
            # 创建触发器并添加任务
            if task_config["schedule_type"] == 'cron':
                trigger = CronTrigger(**task_config["schedule_params"])
            else:
                trigger = IntervalTrigger(**task_config["schedule_params"])
            
            job = self.scheduler.add_job(
                func=self._execute_scan_task,
                trigger=trigger,
                args=[task_id],
                id=task_id,
                name=f"STRM扫描任务: {task_config['directory']}",
                replace_existing=True
            )
            
            task_config["job"] = job
            task_config["enabled"] = True
            
            logger.info(f"启用定时任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"启用任务失败: {e}")
            return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task_config = self.tasks[task_id]
        
        if not task_config["enabled"]:
            logger.warning(f"任务已禁用: {task_id}")
            return True
        
        try:
            # 从调度器中移除
            if self.scheduler and self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
            
            task_config["enabled"] = False
            if "job" in task_config:
                del task_config["job"]
            
            logger.info(f"禁用定时任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"禁用任务失败: {e}")
            return False
    
    def _execute_scan_task(self, task_id: str):
        """执行扫描任务"""
        if task_id not in self.tasks:
            logger.error(f"执行任务时未找到配置: {task_id}")
            return
        
        task_config = self.tasks[task_id]
        start_time = datetime.now()
        
        logger.info(f"开始执行定时扫描任务: {task_id}")
        
        try:
            # 执行扫描
            result = self.scanner.scan_directory(
                directory=task_config["directory"],
                target_formats=task_config["target_formats"],
                recursive=task_config["recursive"],
                dry_run=False
            )
            
            # 更新任务统计
            task_config["last_run"] = start_time
            task_config["run_count"] += 1
            
            # 记录结果
            logger.info(
                f"定时任务 {task_id} 执行完成: "
                f"处理 {result['processed']} 个文件, "
                f"创建 {result['created_links']} 个软链接, "
                f"耗时 {result['duration']:.2f}秒"
            )
            
            # 通知回调
            self._notify_callbacks({
                "event": "task_completed",
                "task_id": task_id,
                "start_time": start_time,
                "result": result,
                "task_config": task_config
            })
            
        except Exception as e:
            logger.error(f"执行定时任务 {task_id} 时出错: {e}")
            
            # 通知回调
            self._notify_callbacks({
                "event": "task_error",
                "task_id": task_id,
                "start_time": start_time,
                "error": str(e),
                "task_config": task_config
            })
    
    def run_task_now(self, task_id: str) -> bool:
        """立即运行指定任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        try:
            # 在后台线程中执行
            thread = threading.Thread(
                target=self._execute_scan_task,
                args=[task_id],
                name=f"ManualTask-{task_id}"
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"手动触发任务执行: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"手动执行任务失败: {e}")
            return False
    
    def get_tasks(self) -> List[Dict]:
        """获取所有任务列表"""
        tasks = []
        
        for task_id, config in self.tasks.items():
            task_info = {
                "task_id": task_id,
                "directory": config["directory"],
                "target_formats": config["target_formats"],
                "schedule_type": config["schedule_type"],
                "schedule_params": config["schedule_params"],
                "recursive": config["recursive"],
                "enabled": config["enabled"],
                "created_at": config["created_at"].isoformat() if config["created_at"] else None,
                "last_run": config["last_run"].isoformat() if config["last_run"] else None,
                "run_count": config["run_count"],
                "next_run": None
            }
            
            # 获取下次运行时间
            if config["enabled"] and self.scheduler:
                job = self.scheduler.get_job(task_id)
                if job and job.next_run_time:
                    task_info["next_run"] = job.next_run_time.isoformat()
            
            tasks.append(task_info)
        
        return tasks
    
    def add_callback(self, callback: Callable):
        """添加任务执行回调"""
        if callback not in self.job_callbacks:
            self.job_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除任务执行回调"""
        if callback in self.job_callbacks:
            self.job_callbacks.remove(callback)
    
    def _notify_callbacks(self, event_data: Dict):
        """通知所有回调函数"""
        for callback in self.job_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"任务回调函数执行失败: {e}")
    
    def get_running_status(self) -> bool:
        """检查调度器是否正在运行"""
        return self.is_running and self.scheduler and self.scheduler.running
