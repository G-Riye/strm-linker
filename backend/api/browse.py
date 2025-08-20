"""
目录浏览 API
提供目录结构浏览和路径补全功能
"""

import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class DirectoryItem(BaseModel):
    """目录项模型"""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    modified_time: Optional[str] = None
    has_strm_files: Optional[bool] = None

class BrowseResult(BaseModel):
    """浏览结果模型"""
    current_path: str
    parent_path: Optional[str]
    items: List[DirectoryItem]
    total_items: int
    directories_count: int
    files_count: int

@router.get("/", response_model=BrowseResult)
async def browse_directory(
    path: str = Query(default=".", description="要浏览的目录路径"),
    show_files: bool = Query(default=False, description="是否显示文件"),
    show_hidden: bool = Query(default=False, description="是否显示隐藏文件/目录"),
    check_strm: bool = Query(default=True, description="是否检查目录中是否包含.strm文件")
):
    """
    浏览指定目录
    
    返回目录中的子目录和文件列表，支持过滤选项
    """
    try:
        # 处理路径
        if path == "." or path == "":
            current_path = Path.cwd()
        else:
            current_path = Path(path).resolve()
        
        # 检查路径是否存在且为目录
        if not current_path.exists():
            raise HTTPException(status_code=404, detail=f"路径不存在: {path}")
        
        if not current_path.is_dir():
            raise HTTPException(status_code=400, detail=f"路径不是目录: {path}")
        
        # 检查访问权限
        if not os.access(current_path, os.R_OK):
            raise HTTPException(status_code=403, detail=f"无权限访问目录: {path}")
        
        items = []
        directories_count = 0
        files_count = 0
        
        try:
            # 遍历目录内容
            for item_path in current_path.iterdir():
                # 跳过隐藏文件/目录（除非特别要求显示）
                if not show_hidden and item_path.name.startswith('.'):
                    continue
                
                is_directory = item_path.is_dir()
                
                # 如果只显示目录，跳过文件
                if not show_files and not is_directory:
                    continue
                
                # 获取基本信息
                try:
                    stat_info = item_path.stat()
                    size = stat_info.st_size if not is_directory else None
                    modified_time = stat_info.st_mtime
                    
                    # 格式化修改时间
                    import datetime
                    modified_time_str = datetime.datetime.fromtimestamp(modified_time).isoformat()
                    
                except (OSError, PermissionError):
                    size = None
                    modified_time_str = None
                
                # 检查目录中是否包含 .strm 文件
                has_strm_files = None
                if is_directory and check_strm:
                    try:
                        has_strm_files = any(
                            f.suffix.lower() == '.strm' 
                            for f in item_path.rglob('*.strm')
                        )
                    except (OSError, PermissionError):
                        has_strm_files = None
                
                # 创建目录项
                directory_item = DirectoryItem(
                    name=item_path.name,
                    path=str(item_path),
                    is_directory=is_directory,
                    size=size,
                    modified_time=modified_time_str,
                    has_strm_files=has_strm_files
                )
                
                items.append(directory_item)
                
                # 统计
                if is_directory:
                    directories_count += 1
                else:
                    files_count += 1
        
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"无权限读取目录内容: {path}")
        
        # 按名称排序：目录在前，文件在后
        items.sort(key=lambda x: (not x.is_directory, x.name.lower()))
        
        # 获取父目录路径
        parent_path = str(current_path.parent) if current_path.parent != current_path else None
        
        result = BrowseResult(
            current_path=str(current_path),
            parent_path=parent_path,
            items=items,
            total_items=len(items),
            directories_count=directories_count,
            files_count=files_count
        )
        
        logger.debug(f"浏览目录: {current_path}, 返回 {len(items)} 个项目")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"浏览目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_directories(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    root_path: str = Query(default=".", description="搜索根目录"),
    max_depth: int = Query(default=3, ge=1, le=10, description="最大搜索深度"),
    max_results: int = Query(default=50, ge=1, le=200, description="最大返回结果数")
):
    """
    搜索目录
    
    在指定路径下搜索包含关键词的目录名
    """
    try:
        # 处理根路径
        if root_path == "." or root_path == "":
            search_root = Path.cwd()
        else:
            search_root = Path(root_path).resolve()
        
        if not search_root.exists() or not search_root.is_dir():
            raise HTTPException(status_code=400, detail=f"搜索根目录无效: {root_path}")
        
        results = []
        query_lower = query.lower()
        
        def search_recursive(path: Path, current_depth: int):
            """递归搜索目录"""
            if current_depth > max_depth or len(results) >= max_results:
                return
            
            try:
                for item in path.iterdir():
                    if len(results) >= max_results:
                        break
                    
                    if not item.is_dir():
                        continue
                    
                    # 跳过隐藏目录
                    if item.name.startswith('.'):
                        continue
                    
                    # 检查目录名是否匹配
                    if query_lower in item.name.lower():
                        # 检查是否包含 .strm 文件
                        try:
                            has_strm_files = any(
                                f.suffix.lower() == '.strm' 
                                for f in item.rglob('*.strm')
                            )
                        except (OSError, PermissionError):
                            has_strm_files = None
                        
                        results.append({
                            "name": item.name,
                            "path": str(item),
                            "relative_path": str(item.relative_to(search_root)),
                            "depth": current_depth,
                            "has_strm_files": has_strm_files
                        })
                    
                    # 递归搜索子目录
                    if current_depth < max_depth:
                        search_recursive(item, current_depth + 1)
            
            except (PermissionError, OSError):
                # 跳过无法访问的目录
                pass
        
        # 开始搜索
        search_recursive(search_root, 1)
        
        logger.info(f"搜索目录 '{query}': 在 {search_root} 中找到 {len(results)} 个结果")
        
        return {
            "query": query,
            "root_path": str(search_root),
            "results": results,
            "total_found": len(results),
            "max_results_reached": len(results) >= max_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autocomplete")
async def autocomplete_path(
    partial_path: str = Query(..., description="部分路径"),
    limit: int = Query(default=10, ge=1, le=50, description="返回建议数量限制")
):
    """
    路径自动补全
    
    根据部分路径返回可能的完整路径建议
    """
    try:
        suggestions = []
        
        # 处理路径
        path = Path(partial_path)
        
        if path.is_absolute():
            # 绝对路径
            if path.exists() and path.is_dir():
                # 路径存在且是目录，返回其子目录
                parent = path
            else:
                # 路径不完整，尝试获取父目录
                parent = path.parent
                prefix = path.name
        else:
            # 相对路径
            parent = Path.cwd() / path.parent
            prefix = path.name
        
        # 检查父目录是否存在且可访问
        if not parent.exists() or not parent.is_dir() or not os.access(parent, os.R_OK):
            return {
                "partial_path": partial_path,
                "suggestions": [],
                "message": "父目录不存在或无法访问"
            }
        
        try:
            # 获取匹配的子目录
            prefix_lower = prefix.lower() if 'prefix' in locals() else ""
            
            for item in parent.iterdir():
                if len(suggestions) >= limit:
                    break
                
                # 只考虑目录
                if not item.is_dir():
                    continue
                
                # 跳过隐藏目录
                if item.name.startswith('.'):
                    continue
                
                # 如果有前缀，检查匹配
                if 'prefix' in locals() and prefix:
                    if not item.name.lower().startswith(prefix_lower):
                        continue
                
                # 添加建议
                full_path = str(item)
                
                # 检查是否包含 .strm 文件（可选）
                try:
                    has_strm_files = any(
                        f.suffix.lower() == '.strm' 
                        for f in item.rglob('*.strm')
                    )
                except (OSError, PermissionError):
                    has_strm_files = None
                
                suggestions.append({
                    "path": full_path,
                    "name": item.name,
                    "has_strm_files": has_strm_files
                })
        
        except (PermissionError, OSError):
            pass
        
        logger.debug(f"路径自动补全 '{partial_path}': 返回 {len(suggestions)} 个建议")
        
        return {
            "partial_path": partial_path,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"路径自动补全失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drives")
async def get_system_drives():
    """
    获取系统驱动器列表 (Windows) 或常用目录 (Linux/macOS)
    
    用于目录选择器的根级别选项
    """
    try:
        drives = []
        
        if os.name == 'nt':  # Windows
            import string
            import subprocess
            
            # 获取可用的驱动器
            available_drives = ['%s:' % d for d in string.ascii_uppercase 
                               if os.path.exists('%s:\\' % d)]
            
            for drive in available_drives:
                drive_path = f"{drive}\\"
                try:
                    # 检查驱动器是否可访问
                    if os.access(drive_path, os.R_OK):
                        # 尝试获取驱动器标签
                        display_name = drive
                        try:
                            # 优先使用 win32api
                            import win32api
                            label = win32api.GetVolumeInformation(drive_path)[0]
                            display_name = f"{drive} ({label})" if label else drive
                        except ImportError:
                            try:
                                # 备选方案：使用 wmic 命令
                                result = subprocess.run(
                                    ['wmic', 'logicaldisk', 'where', f'caption="{drive}"', 'get', 'volumename'],
                                    capture_output=True, text=True, timeout=3
                                )
                                if result.returncode == 0:
                                    lines = result.stdout.strip().split('\n')
                                    if len(lines) > 1:
                                        label = lines[1].strip()
                                        if label:
                                            display_name = f"{drive} ({label})"
                            except:
                                pass
                        except Exception:
                            pass
                        
                        drives.append({
                            "path": drive_path,
                            "name": display_name,
                            "type": "drive"
                        })
                except Exception:
                    continue
        
        else:  # Linux/macOS
            # 常用目录
            common_dirs = [
                {"path": "/", "name": "根目录 (/)", "type": "root"},
                {"path": "/home", "name": "用户目录 (/home)", "type": "directory"},
                {"path": "/media", "name": "媒体 (/media)", "type": "directory"},
                {"path": "/mnt", "name": "挂载点 (/mnt)", "type": "directory"},
                {"path": "/opt", "name": "可选软件 (/opt)", "type": "directory"},
                {"path": "/var", "name": "变量数据 (/var)", "type": "directory"}
            ]
            
            # 检查目录是否存在且可访问
            for dir_info in common_dirs:
                if os.path.exists(dir_info["path"]) and os.access(dir_info["path"], os.R_OK):
                    drives.append(dir_info)
            
            # 添加用户主目录
            home_dir = os.path.expanduser("~")
            if os.path.exists(home_dir):
                drives.append({
                    "path": home_dir,
                    "name": f"主目录 ({os.path.basename(home_dir)})",
                    "type": "home"
                })
        
        return {
            "drives": drives,
            "current_os": "windows" if os.name == 'nt' else "unix"
        }
        
    except Exception as e:
        logger.error(f"获取系统驱动器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
