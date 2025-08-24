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
    
    def __init__(self, custom_video_extensions: Optional[List[str]] = None, custom_metadata_extensions: Optional[List[str]] = None):
        # 默认支持的视频扩展名
        default_video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mts', '.3gp', '.ogv', '.rmvb', '.asf', '.divx', '.xvid'}
        
        # 默认支持的元数据扩展名（影视库常用格式）
        default_metadata_extensions = {
            # 字幕文件
            '.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx', '.smi', '.sami', '.rt', '.txt',
            # 元数据文件
            '.nfo', '.xml', '.json', '.yaml', '.yml',
            # 图片文件
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            # 影视库专用图片
            '.tbn', '.fanart.jpg', '.poster.jpg', '.banner.jpg', '.clearart.png', '.clearlogo.png', 
            '.disc.png', '.landscape.jpg', '.logo.png', '.thumb.jpg', '.season01.jpg', '.season02.jpg',
            # 音频文件
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
            # 其他元数据
            '.sfv', '.md5', '.sha1', '.sha256', '.info', '.desc', '.plot', '.tag'
        }
        
        # 合并用户自定义扩展名
        self.video_extensions = default_video_extensions.copy()
        if custom_video_extensions:
            for ext in custom_video_extensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                self.video_extensions.add(ext.lower())
        
        self.metadata_extensions = default_metadata_extensions.copy()
        if custom_metadata_extensions:
            for ext in custom_metadata_extensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                self.metadata_extensions.add(ext.lower())
        
        # STRM 文件匹配模式：xxx.(ext).strm
        self.strm_pattern = re.compile(r'(.+)\.\(([^.]+)\)\.strm$', re.IGNORECASE)
        
        # 操作系统检测
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
    
    def get_supported_extensions(self) -> Dict[str, Set[str]]:
        """获取支持的扩展名列表"""
        return {
            "video_extensions": self.video_extensions,
            "metadata_extensions": self.metadata_extensions
        }
    
    def add_video_extension(self, extension: str):
        """添加自定义视频扩展名"""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.video_extensions.add(extension.lower())
        logger.info(f"添加视频扩展名: {extension}")
    
    def add_metadata_extension(self, extension: str):
        """添加自定义元数据扩展名"""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.metadata_extensions.add(extension.lower())
        logger.info(f"添加元数据扩展名: {extension}")
    
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
            target_formats: 目标视频格式列表（已废弃，保留兼容性）
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
        logger.info(f"支持的视频格式: {', '.join(sorted(self.video_extensions))}")
        logger.info(f"支持的元数据格式: {', '.join(sorted(self.metadata_extensions))}")
        
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
                "skipped": 0,
                "errors": [],
                "details": [],
                "duration": time.time() - start_time
            }
        
        # 处理软链接创建
        results = self._process_strm_files(strm_files, dry_run)
        
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
                if file_path.is_file() and self._is_valid_strm(file_path):
                    strm_files.append(file_path)
        
        except Exception as e:
            logger.error(f"搜索 .strm 文件时出错: {e}")
        
        return strm_files
    
    def _is_valid_strm(self, strm_path: Path) -> bool:
        """判断是否是有效的 .strm 文件"""
        match = self.strm_pattern.match(strm_path.name)
        if not match:
            return False
        
        # 检查扩展名是否在支持的视频格式中
        extension = match.group(2).lower()
        return f'.{extension}' in self.video_extensions
    
    def _process_strm_files(
        self, 
        strm_files: List[Path], 
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
            
            base_name = match.group(1)  # 基础文件名
            video_ext = match.group(2)  # 视频扩展名
            
            parent_dir = strm_file.parent
            links_created = 0
            created_links = []
            
            # 1. 创建视频软链接 (xxx.mp4 -> xxx.(mp4).strm)
            video_link_name = f"{base_name}.{video_ext}"
            video_link_path = parent_dir / video_link_name
            
            if not video_link_path.exists():
                if not dry_run:
                    try:
                        if self.is_windows and not self.has_admin_rights:
                            # Windows 下没有管理员权限，尝试创建硬链接
                            try:
                                video_link_path.hardlink_to(strm_file)
                                logger.info(f"创建视频硬链接: {video_link_path} -> {strm_file}")
                                links_created += 1
                                created_links.append(str(video_link_path))
                            except OSError:
                                # 如果硬链接也失败，尝试复制文件
                                import shutil
                                shutil.copy2(strm_file, video_link_path)
                                logger.info(f"复制视频文件: {video_link_path} <- {strm_file}")
                                links_created += 1
                                created_links.append(str(video_link_path))
                        else:
                            video_link_path.symlink_to(strm_file)
                            logger.info(f"创建视频软链接: {video_link_path} -> {strm_file}")
                            links_created += 1
                            created_links.append(str(video_link_path))
                    except OSError as e:
                        logger.error(f"创建视频链接失败: {e}")
                        return {
                            "success": False,
                            "error": f"创建视频链接失败: {str(e)}",
                            "links_created": 0
                        }
                else:
                    links_created += 1
                    created_links.append(str(video_link_path))
                    logger.info(f"[预览] 将创建视频软链接: {video_link_path} -> {strm_file}")
            
            # 2. 查找并创建对应的元数据软链接
            metadata_links_created = self._create_metadata_links(
                parent_dir, base_name, video_ext, dry_run
            )
            links_created += metadata_links_created["count"]
            created_links.extend(metadata_links_created["links"])
            
            return {
                "success": True,
                "links_created": links_created,
                "created_links": created_links,
                "base_name": base_name,
                "video_extension": video_ext
            }
            
        except Exception as e:
            logger.error(f"处理 .strm 文件 {strm_file} 时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "links_created": 0
            }
    
    def _create_metadata_links(
        self, 
        parent_dir: Path, 
        base_name: str, 
        video_ext: str, 
        dry_run: bool
    ) -> Dict[str, any]:
        """创建元数据软链接"""
        links_created = 0
        created_links = []
        
        # 查找所有可能的元数据文件
        for metadata_ext in self.metadata_extensions:
            # 查找源元数据文件 (xxx.nfo, xxx.srt 等)
            source_metadata_file = parent_dir / f"{base_name}{metadata_ext}"
            
            if source_metadata_file.exists():
                # 创建对应的元数据软链接 (xxx.(mp4).nfo -> xxx.nfo)
                metadata_link_name = f"{base_name}.({video_ext}){metadata_ext}"
                metadata_link_path = parent_dir / metadata_link_name
                
                if not metadata_link_path.exists():
                    if not dry_run:
                        try:
                            if self.is_windows and not self.has_admin_rights:
                                # Windows 下没有管理员权限，尝试创建硬链接
                                try:
                                    metadata_link_path.hardlink_to(source_metadata_file)
                                    logger.info(f"创建元数据硬链接: {metadata_link_path} -> {source_metadata_file}")
                                    links_created += 1
                                    created_links.append(str(metadata_link_path))
                                except OSError:
                                    # 如果硬链接也失败，尝试复制文件
                                    import shutil
                                    shutil.copy2(source_metadata_file, metadata_link_path)
                                    logger.info(f"复制元数据文件: {metadata_link_path} <- {source_metadata_file}")
                                    links_created += 1
                                    created_links.append(str(metadata_link_path))
                            else:
                                metadata_link_path.symlink_to(source_metadata_file)
                                logger.info(f"创建元数据软链接: {metadata_link_path} -> {source_metadata_file}")
                                links_created += 1
                                created_links.append(str(metadata_link_path))
                        except OSError as e:
                            logger.error(f"创建元数据链接失败: {metadata_link_path} -> {source_metadata_file}: {e}")
                            # 继续处理其他文件，不中断整个流程
                    else:
                        links_created += 1
                        created_links.append(str(metadata_link_path))
                        logger.info(f"[预览] 将创建元数据软链接: {metadata_link_path} -> {source_metadata_file}")
        
        return {
            "count": links_created,
            "links": created_links
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
