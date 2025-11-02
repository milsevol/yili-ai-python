"""
日期时间工具 - 提供日期和时间相关的功能
"""

from datetime import datetime, timezone
from langchain_core.tools import tool


@tool
def current_date() -> str:
    """
    获取当前日期
    
    返回格式：YYYY-MM-DD
    例如：2024-01-15
    """
    return datetime.now().strftime("%Y-%m-%d")


@tool
def current_time() -> str:
    """
    获取当前时间
    
    返回格式：YYYY-MM-DD HH:MM:SS
    例如：2024-01-15 14:30:25
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def current_timestamp() -> str:
    """
    获取当前时间戳
    
    返回Unix时间戳（秒）
    """
    return str(int(datetime.now().timestamp()))


@tool
def current_utc_time() -> str:
    """
    获取当前UTC时间
    
    返回格式：YYYY-MM-DD HH:MM:SS UTC
    """
    utc_time = datetime.now(timezone.utc)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S UTC")