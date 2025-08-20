"""
文件系统监听服务
实时监控指定目录的 .strm 文件变化并自动处理
"""

import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

from services.logger import get_logger
from services.scanner import StrmScanner

logger = get_logger(__name__)

class StrmFileHandler(FileSystemEventHandler):
    """STRM 文件事件处理器"""
    
    def __init__(self, scanner: StrmScanner, target_formats: List[str], callback: Optional[Callable] = None):
        super().__init__()
        self.scanner = scanner
        self.target_formats = target_formats
        self.callback = callback
        self._processing = set()  # 防止重复处理
        self._lock = threading.Lock()
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and event.src_path.endswith('.strm'):
            self._handle_strm_file(event.src_path, "created")
    
    def on_moved(self, event):
        """文件移动事件"""
        if not event.is_directory:
            # 处理移动到的新文件
            if event.dest_path.endswith('.strm'):
                self._handle_strm_file(event.dest_path, "moved")
    
    def _handle_strm_file(self, file_path: str, event_type: str):
        """处理 STRM 文件事件"""
        file_path = Path(file_path)
        
        # 防止重复处理
        with self._lock:
            if str(file_path) in self._processing:
                return
            self._processing.add(str(file_path))
        
        try:
            # 验证是否是有效的视频 .strm 文件
            if not self.scanner._is_video_strm(file_path):
                return
            
            logger.info(f"检测到 .strm 文件 {event_type}: {file_path}")
            
            # 处理单个文件
            result = self.scanner._process_single_strm(
                file_path, 
                self.target_formats, 
                dry_run=False
            )
            
            if result["success"]:
                logger.info(f"成功处理 {file_path}, 创建了 {result['links_created']} 个软链接")
                
                # 调用回调函数（如果有）
                if self.callback:
                    self.callback({
                        "event": "file_processed",
                        "file": str(file_path),
                        "event_type": event_type,
                        "result": result,
                        "timestamp": threading.current_thread().ident
                    })
            else:
                logger.error(f"处理 {file_path} 失败: {result.get('error', '未知错误')}")
                
                if self.callback:
                    self.callback({
                        "event": "file_error", 
                        "file": str(file_path),
                        "event_type": event_type,
                        "error": result.get('error', '未知错误'),
                        "timestamp": threading.current_thread().ident
                    })
        
        except Exception as e:
            logger.error(f"处理文件事件时出错: {e}")
            if self.callback:
                self.callback({
                    "event": "processing_error",
                    "file": str(file_path),
                    "error": str(e),
                    "timestamp": threading.current_thread().ident
                })
        
        finally:
            # 移除处理标记
            with self._lock:
                self._processing.discard(str(file_path))

class WatcherService:
    """文件监听服务"""
    
    def __init__(self):
        self.observer = None
        self.scanner = StrmScanner()
        self.watch_dirs = {}  # 监听目录配置
        self.is_running = False
        self._lock = threading.Lock()
        self.event_callbacks = []  # 事件回调函数列表
    
    def add_watch_directory(
        self, 
        directory: str, 
        target_formats: Optional[List[str]] = None,
        recursive: bool = True
    ) -> bool:
        """添加监听目录"""
        directory = Path(directory).resolve()
        
        if not directory.exists():
            logger.error(f"监听目录不存在: {directory}")
            return False
        
        if not directory.is_dir():
            logger.error(f"路径不是目录: {directory}")
            return False
        
        with self._lock:
            dir_key = str(directory)
            
            if dir_key in self.watch_dirs:
                logger.warning(f"目录已在监听中: {directory}")
                return True
            
            # 默认目标格式
            if not target_formats:
                target_formats = ['mp4', 'mkv']
            
            self.watch_dirs[dir_key] = {
                "path": directory,
                "target_formats": target_formats,
                "recursive": recursive,
                "handler": None
            }
            
            logger.info(f"添加监听目录: {directory} (格式: {target_formats}, 递归: {recursive})")
            
            # 如果服务正在运行，立即开始监听
            if self.is_running and self.observer:
                self._start_watch_single_dir(dir_key)
            
            return True
    
    def remove_watch_directory(self, directory: str) -> bool:
        """移除监听目录"""
        directory = str(Path(directory).resolve())
        
        with self._lock:
            if directory not in self.watch_dirs:
                logger.warning(f"目录未在监听中: {directory}")
                return False
            
            # 停止对该目录的监听
            if self.observer and self.watch_dirs[directory]["handler"]:
                self.observer.unschedule(self.watch_dirs[directory]["handler"])
            
            del self.watch_dirs[directory]
            logger.info(f"移除监听目录: {directory}")
            return True
    
    def start(self) -> bool:
        """启动监听服务"""
        with self._lock:
            if self.is_running:
                logger.warning("监听服务已经在运行")
                return True
            
            if not self.watch_dirs:
                logger.warning("没有配置监听目录")
                return False
            
            try:
                self.observer = Observer()
                
                # 为每个目录设置监听
                for dir_key in self.watch_dirs.keys():
                    self._start_watch_single_dir(dir_key)
                
                self.observer.start()
                self.is_running = True
                
                logger.info(f"文件监听服务启动成功，监听 {len(self.watch_dirs)} 个目录")
                return True
                
            except Exception as e:
                logger.error(f"启动监听服务失败: {e}")
                self.is_running = False
                return False
    
    def stop(self) -> bool:
        """停止监听服务"""
        with self._lock:
            if not self.is_running:
                logger.warning("监听服务未在运行")
                return True
            
            try:
                if self.observer:
                    self.observer.stop()
                    self.observer.join(timeout=5)  # 等待最多5秒
                    self.observer = None
                
                self.is_running = False
                logger.info("文件监听服务已停止")
                return True
                
            except Exception as e:
                logger.error(f"停止监听服务失败: {e}")
                return False
    
    def _start_watch_single_dir(self, dir_key: str):
        """为单个目录启动监听"""
        config = self.watch_dirs[dir_key]
        
        # 创建事件处理器
        handler = StrmFileHandler(
            self.scanner,
            config["target_formats"],
            self._notify_callbacks
        )
        
        # 添加监听
        watch = self.observer.schedule(
            handler,
            str(config["path"]),
            recursive=config["recursive"]
        )
        
        # 保存处理器引用
        config["handler"] = watch
        
        logger.info(f"开始监听目录: {config['path']}")
    
    def add_callback(self, callback: Callable):
        """添加事件回调函数"""
        if callback not in self.event_callbacks:
            self.event_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除事件回调函数"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def _notify_callbacks(self, event_data: Dict):
        """通知所有回调函数"""
        for callback in self.event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    def get_running_status(self) -> bool:
        """检查服务是否正在运行"""
        return self.is_running
    
    def get_watch_status(self) -> Dict:
        """获取监听状态"""
        return {
            "is_running": self.is_running,
            "watch_directories": [
                {
                    "path": str(config["path"]),
                    "target_formats": config["target_formats"],
                    "recursive": config["recursive"]
                }
                for config in self.watch_dirs.values()
            ]
        }
