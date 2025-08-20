"""
日志服务模块
提供统一的日志管理和查询功能
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pythonjsonlogger import jsonlogger
import threading

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "strm_linker.log"
        self._lock = threading.Lock()
        
        # 配置日志格式
        self.formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        
        # 设置日志处理器
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 文件处理器
        file_handler = logging.FileHandler(
            self.log_file, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(self.formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        return file_handler, console_handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        logger = logging.getLogger(name)
        
        if not logger.handlers:
            file_handler, console_handler = self._setup_handlers()
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def get_logs(
        self, 
        limit: int = 100, 
        level: Optional[str] = None,
        search: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取日志记录
        
        Args:
            limit: 最大返回条数
            level: 日志级别过滤
            search: 搜索关键词
            start_time: 开始时间
            end_time: 结束时间
        """
        logs = []
        
        if not self.log_file.exists():
            return logs
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # 解析时间
                        log_time = datetime.fromisoformat(
                            log_entry.get('asctime', '').replace('Z', '+00:00')
                        )
                        
                        # 时间范围过滤
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                        
                        # 级别过滤
                        if level and log_entry.get('levelname') != level.upper():
                            continue
                        
                        # 关键词搜索
                        if search:
                            message = log_entry.get('message', '').lower()
                            if search.lower() not in message:
                                continue
                        
                        logs.append(log_entry)
                        
                    except (json.JSONDecodeError, ValueError):
                        # 忽略无效的日志行
                        continue
        
        except Exception as e:
            self.get_logger(__name__).error(f"读取日志文件失败: {e}")
        
        # 按时间倒序排列，返回最新的记录
        logs.sort(key=lambda x: x.get('asctime', ''), reverse=True)
        return logs[:limit]
    
    def clear_old_logs(self, days: int = 7):
        """清理指定天数之前的日志"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        if not self.log_file.exists():
            return
        
        try:
            valid_logs = []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(
                            log_entry.get('asctime', '').replace('Z', '+00:00')
                        )
                        
                        if log_time >= cutoff_time:
                            valid_logs.append(line.strip())
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # 重写日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                for log_line in valid_logs:
                    f.write(log_line + '\n')
            
            self.get_logger(__name__).info(f"清理了 {days} 天前的日志")
            
        except Exception as e:
            self.get_logger(__name__).error(f"清理日志失败: {e}")

# 全局日志管理器实例
log_manager = LogManager()

def setup_logging() -> logging.Logger:
    """设置并返回主应用日志器"""
    return log_manager.get_logger("strm_linker")

def get_logger(name: str) -> logging.Logger:
    """获取指定模块的日志器"""
    return log_manager.get_logger(name)
