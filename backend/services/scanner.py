"""
核心扫描和软链逻辑模块
负责扫描 .strm 文件并创建对应的软链接
"""

import os
import re
import sys
import ctypes
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.logger import get_logger

logger = get_logger(__name__)

class StrmScanner:
    """STRM 文件扫描器和软链管理器"""
    
    def __init__(self):
        self.supported_video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}
        self.subtitle_exts = {'.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx'}
        self.strm_pattern = re.compile(r'(.+)\.(mp4|mkv|avi|mov|wmv|flv|webm)\.strm$', re.IGNORECASE)
        self.is_windows = os.name == 'nt'
        self.has_admin_rights = self._check_admin_rights() if self.is_windows else True
    
    def _check_admin_rights(self) -> bool:
        """检查 Windows 管理员权限"""
        if not self.is_windows:
            return True
        
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def scan_directory(
        self, 
        directory: str, 
        target_formats: Optional[List[str]] = None,
        recursive: bool = True,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        扫描目录中的 .strm 文件并处理软链接
        
        Args:
            directory: 扫描的目录路径
            target_formats: 目标视频格式列表（如 ['mp4', 'mkv']）
            recursive: 是否递归扫描子目录
            dry_run: 是否只是预览不实际执行
            
        Returns:
            包含扫描结果的字典
        """
        start_time = time.time()
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")
        
        logger.info(f"开始扫描目录: {directory} (递归: {recursive}, 预览模式: {dry_run})")
        
        # 收集所有 .strm 文件
        strm_files = self._find_strm_files(directory_path, recursive)
        logger.info(f"找到 {len(strm_files)} 个 .strm 文件")
        
        if not strm_files:
            return {
                "success": True,
                "directory": directory,
                "total_files": 0,
                "processed": 0,
                "created_links": 0,
                "errors": [],
                "duration": time.time() - start_time
            }
        
        # 处理软链接创建
        results = self._process_strm_files(
            strm_files, 
            target_formats or ['mp4', 'mkv'],
            dry_run
        )
        
        duration = time.time() - start_time
        logger.info(f"扫描完成，耗时: {duration:.2f}秒")
        
        return {
            "success": True,
            "directory": directory,
            "total_files": len(strm_files),
            "processed": results["processed"],
            "created_links": results["created"],
            "skipped": results["skipped"],
            "errors": results["errors"],
            "details": results["details"],
            "duration": duration
        }
    
    def _find_strm_files(self, directory: Path, recursive: bool) -> List[Path]:
        """查找目录中的所有 .strm 文件"""
        strm_files = []
        
        try:
            if recursive:
                pattern = "**/*.strm"
            else:
                pattern = "*.strm"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file() and self._is_video_strm(file_path):
                    strm_files.append(file_path)
        
        except Exception as e:
            logger.error(f"搜索 .strm 文件时出错: {e}")
        
        return strm_files
    
    def _is_video_strm(self, strm_path: Path) -> bool:
        """判断是否是视频格式的 .strm 文件"""
        match = self.strm_pattern.match(strm_path.name)
        return match is not None
    
    def _process_strm_files(
        self, 
        strm_files: List[Path], 
        target_formats: List[str],
        dry_run: bool
    ) -> Dict[str, any]:
        """批量处理 .strm 文件"""
        processed = 0
        created = 0
        skipped = 0
        errors = []
        details = []
        
        # 使用线程池提高处理效率
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(
                    self._process_single_strm, 
                    strm_file, 
                    target_formats, 
                    dry_run
                ): strm_file 
                for strm_file in strm_files
            }
            
            # 收集结果
            for future in as_completed(future_to_file):
                strm_file = future_to_file[future]
                
                try:
                    result = future.result()
                    processed += 1
                    
                    if result["success"]:
                        created += result["links_created"]
                        if result["links_created"] == 0:
                            skipped += 1
                    else:
                        errors.append({
                            "file": str(strm_file),
                            "error": result["error"]
                        })
                    
                    details.append({
                        "file": str(strm_file),
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"处理文件 {strm_file} 时出错: {e}")
                    errors.append({
                        "file": str(strm_file),
                        "error": str(e)
                    })
        
        return {
            "processed": processed,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "details": details
        }
    
    def _process_single_strm(
        self, 
        strm_file: Path, 
        target_formats: List[str],
        dry_run: bool
    ) -> Dict[str, any]:
        """处理单个 .strm 文件"""
        try:
            # 解析文件名
            match = self.strm_pattern.match(strm_file.name)
            if not match:
                return {
                    "success": False,
                    "error": "无法解析 .strm 文件名格式",
                    "links_created": 0
                }
            
            base_name = match.group(1)  # 去掉格式后缀的基础文件名
            original_ext = match.group(2)  # 原始视频格式
            
            parent_dir = strm_file.parent
            links_created = 0
            created_links = []
            
            # 为每种目标格式创建软链接
            for target_ext in target_formats:
                if target_ext.lower() == original_ext.lower():
                    continue  # 跳过原始格式
                
                target_name = f"{base_name}.{target_ext}"
                target_path = parent_dir / target_name
                
                # 检查目标文件是否已存在
                if target_path.exists():
                    logger.debug(f"目标文件已存在，跳过: {target_path}")
                    continue
                
                # 创建软链接
                if not dry_run:
                    try:
                        if self.is_windows:
                            # Windows 权限检查
                            if not self.has_admin_rights:
                                logger.warning("Windows 下创建符号链接需要管理员权限，尝试创建硬链接")
                                # 尝试创建硬链接作为备选方案
                                try:
                                    target_path.hardlink_to(strm_file)
                                    logger.info(f"创建硬链接: {target_path} -> {strm_file}")
                                except OSError:
                                    # 如果硬链接也失败，尝试复制文件
                                    import shutil
                                    shutil.copy2(strm_file, target_path)
                                    logger.info(f"复制文件: {target_path} <- {strm_file}")
                            else:
                                # 有管理员权限，创建符号链接
                                target_path.symlink_to(strm_file)
                                logger.info(f"创建符号链接: {target_path} -> {strm_file}")
                        else:
                            # Linux/macOS - 直接创建符号链接
                            target_path.symlink_to(strm_file)
                            logger.info(f"创建符号链接: {target_path} -> {strm_file}")
                        
                        links_created += 1
                        created_links.append(str(target_path))
                        
                    except OSError as e:
                        error_msg = str(e).lower()
                        if "privilege" in error_msg or "access" in error_msg:
                            return {
                                "success": False,
                                "error": "权限不足。Windows 下建议以管理员权限运行，或启用开发者模式以创建符号链接。",
                                "links_created": 0
                            }
                        else:
                            logger.error(f"创建链接失败: {e}")
                            return {
                                "success": False,
                                "error": f"创建链接失败: {str(e)}",
                                "links_created": 0
                            }
                else:
                    # 预览模式
                    links_created += 1
                    created_links.append(str(target_path))
                    logger.info(f"[预览] 将创建软链接: {target_path} -> {strm_file}")
            
            return {
                "success": True,
                "links_created": links_created,
                "created_links": created_links,
                "base_name": base_name,
                "original_format": original_ext
            }
            
        except Exception as e:
            logger.error(f"处理 .strm 文件 {strm_file} 时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "links_created": 0
            }
    
    def cleanup_broken_links(self, directory: str, recursive: bool = True) -> Dict[str, any]:
        """清理目录中的损坏软链接"""
        start_time = time.time()
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        logger.info(f"开始清理损坏的软链接: {directory}")
        
        removed_count = 0
        errors = []
        
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory_path.glob(pattern):
                if file_path.is_symlink() and not file_path.exists():
                    try:
                        file_path.unlink()
                        removed_count += 1
                        logger.info(f"删除损坏的软链接: {file_path}")
                    except Exception as e:
                        error_msg = f"删除软链接 {file_path} 失败: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
        
        except Exception as e:
            logger.error(f"清理软链接时出错: {e}")
            errors.append(str(e))
        
        duration = time.time() - start_time
        logger.info(f"清理完成，删除了 {removed_count} 个损坏的软链接，耗时: {duration:.2f}秒")
        
        return {
            "success": True,
            "directory": directory,
            "removed_count": removed_count,
            "errors": errors,
            "duration": duration
        }
