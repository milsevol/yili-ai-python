"""
工具模块 - 为LLM提供安全的工具函数
"""

from .math_tools import safe_calculator
from .datetime_tools import current_date, current_time

# 可用工具列表
AVAILABLE_TOOLS = [
    safe_calculator,
    current_date,
    current_time
]

__all__ = [
    'safe_calculator',
    'current_date', 
    'current_time',
    'AVAILABLE_TOOLS'
]