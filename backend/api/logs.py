"""
日志管理 API
提供日志查询和管理功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.logger import log_manager, get_logger

logger = get_logger(__name__)
router = APIRouter()

class LogEntry(BaseModel):
    """日志条目模型"""
    asctime: str
    name: str
    levelname: str
    message: str

class LogQuery(BaseModel):
    """日志查询参数"""
    limit: Optional[int] = 100
    level: Optional[str] = None
    search: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@router.get("/", response_model=List[Dict[str, Any]])
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="返回日志数量"),
    level: Optional[str] = Query(default=None, description="日志级别过滤 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
    start_time: Optional[str] = Query(default=None, description="开始时间 (ISO格式)"),
    end_time: Optional[str] = Query(default=None, description="结束时间 (ISO格式)")
):
    """
    获取日志记录
    
    支持多种过滤条件：
    - limit: 返回的最大日志条数
    - level: 按日志级别过滤
    - search: 按消息内容搜索
    - start_time, end_time: 按时间范围过滤
    """
    try:
        # 解析时间参数
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式错误，请使用 ISO 格式")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式错误，请使用 ISO 格式")
        
        # 验证日志级别
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if level and level.upper() not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的日志级别: {level}. 有效值: {', '.join(valid_levels)}"
            )
        
        # 获取日志
        logs = log_manager.get_logs(
            limit=limit,
            level=level,
            search=search,
            start_time=start_dt,
            end_time=end_dt
        )
        
        logger.info(f"查询日志: 返回 {len(logs)} 条记录")
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/levels")
async def get_log_levels():
    """获取支持的日志级别列表"""
    return {
        "levels": [
            {"value": "DEBUG", "label": "调试", "color": "#909399"},
            {"value": "INFO", "label": "信息", "#409EFF"},
            {"value": "WARNING", "label": "警告", "color": "#E6A23C"},
            {"value": "ERROR", "label": "错误", "color": "#F56C6C"},
            {"value": "CRITICAL", "label": "严重", "color": "#F56C6C"}
        ]
    }

@router.get("/stats")
async def get_log_statistics():
    """获取日志统计信息"""
    try:
        # 获取最近的日志进行统计
        recent_logs = log_manager.get_logs(limit=1000)
        
        if not recent_logs:
            return {
                "total": 0,
                "level_counts": {},
                "recent_errors": 0,
                "latest_log_time": None
            }
        
        # 统计各级别日志数量
        level_counts = {}
        error_count = 0
        
        for log in recent_logs:
            level = log.get('levelname', 'UNKNOWN')
            level_counts[level] = level_counts.get(level, 0) + 1
            
            if level in ['ERROR', 'CRITICAL']:
                error_count += 1
        
        # 最新日志时间
        latest_log_time = recent_logs[0].get('asctime') if recent_logs else None
        
        return {
            "total": len(recent_logs),
            "level_counts": level_counts,
            "recent_errors": error_count,
            "latest_log_time": latest_log_time
        }
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_old_logs(days: int = Query(default=7, ge=1, le=365, description="保留最近几天的日志")):
    """
    清理旧日志
    
    删除指定天数之前的日志记录
    """
    try:
        log_manager.clear_old_logs(days=days)
        
        logger.info(f"清理了 {days} 天前的日志")
        return {"message": f"成功清理 {days} 天前的日志"}
        
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_logs(
    format_type: str = Query(default="json", description="导出格式: json 或 txt"),
    limit: int = Query(default=1000, ge=1, le=10000, description="导出日志数量"),
    level: Optional[str] = Query(default=None, description="日志级别过滤")
):
    """
    导出日志
    
    支持 JSON 和文本格式导出
    """
    try:
        # 获取日志
        logs = log_manager.get_logs(limit=limit, level=level)
        
        if format_type.lower() == "json":
            from fastapi.responses import JSONResponse
            import json
            
            # 返回 JSON 格式
            return JSONResponse(
                content=logs,
                headers={
                    "Content-Disposition": f"attachment; filename=strm_linker_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
            
        elif format_type.lower() == "txt":
            from fastapi.responses import PlainTextResponse
            
            # 转换为文本格式
            text_lines = []
            for log in logs:
                line = f"[{log.get('asctime', '')}] {log.get('levelname', '')} {log.get('name', '')} - {log.get('message', '')}"
                text_lines.append(line)
            
            text_content = '\n'.join(text_lines)
            
            return PlainTextResponse(
                content=text_content,
                headers={
                    "Content-Disposition": f"attachment; filename=strm_linker_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式，支持: json, txt")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_logging():
    """
    测试日志功能
    
    生成各种级别的测试日志
    """
    try:
        test_logger = get_logger("test")
        
        test_logger.debug("这是一条调试日志")
        test_logger.info("这是一条信息日志")
        test_logger.warning("这是一条警告日志")
        test_logger.error("这是一条错误日志")
        test_logger.critical("这是一条严重日志")
        
        return {"message": "测试日志已生成"}
        
    except Exception as e:
        logger.error(f"生成测试日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
