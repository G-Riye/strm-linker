"""
配置管理服务
负责保存和加载扫描配置
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from services.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "scan_configs.json"
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载现有配置
        self._load_configs()
    
    def _load_configs(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.configs = json.load(f)
                logger.info(f"加载了 {len(self.configs)} 个扫描配置")
            else:
                self.configs = {}
                logger.info("创建新的配置文件")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.configs = {}
    
    def _save_configs(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def create_config(self, config_data: Dict[str, Any]) -> str:
        """创建新的扫描配置"""
        config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        config = {
            "config_id": config_id,
            "name": config_data["name"],
            "description": config_data.get("description", ""),
            "directory": config_data["directory"],
            "recursive": config_data.get("recursive", True),
            "custom_video_extensions": config_data.get("custom_video_extensions", []),
            "custom_metadata_extensions": config_data.get("custom_metadata_extensions", []),
            "created_at": now,
            "updated_at": now
        }
        
        self.configs[config_id] = config
        self._save_configs()
        
        logger.info(f"创建扫描配置: {config['name']} (ID: {config_id})")
        return config_id
    
    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取指定配置"""
        return self.configs.get(config_id)
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置"""
        return list(self.configs.values())
    
    def update_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        if config_id not in self.configs:
            return False
        
        config = self.configs[config_id]
        now = datetime.now().isoformat()
        
        # 更新字段
        for key, value in config_data.items():
            if value is not None and key in config:
                config[key] = value
        
        config["updated_at"] = now
        self._save_configs()
        
        logger.info(f"更新扫描配置: {config['name']} (ID: {config_id})")
        return True
    
    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        if config_id not in self.configs:
            return False
        
        config_name = self.configs[config_id]["name"]
        del self.configs[config_id]
        self._save_configs()
        
        logger.info(f"删除扫描配置: {config_name} (ID: {config_id})")
        return True
    
    def get_config_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取配置"""
        for config in self.configs.values():
            if config["name"] == name:
                return config
        return None
    
    def validate_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证配置数据"""
        errors = []
        
        if not config_data.get("name"):
            errors.append("配置名称不能为空")
        
        if not config_data.get("directory"):
            errors.append("扫描目录不能为空")
        else:
            directory_path = Path(config_data["directory"])
            if not directory_path.exists():
                errors.append(f"目录不存在: {config_data['directory']}")
            elif not directory_path.is_dir():
                errors.append(f"路径不是目录: {config_data['directory']}")
        
        return errors
