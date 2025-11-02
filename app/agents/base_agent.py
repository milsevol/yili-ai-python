"""
基础Agent类 - 定义所有Agent的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage


class BaseAgent(ABC):
    """所有Agent的基础类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: List[BaseTool] = []
        self.conversation_history: List[BaseMessage] = []
    
    def add_tool(self, tool: BaseTool):
        """添加工具到Agent"""
        self.tools.append(tool)
    
    def add_tools(self, tools: List[BaseTool]):
        """批量添加工具"""
        self.tools.extend(tools)
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
    
    @abstractmethod
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        执行Agent任务的抽象方法
        
        Args:
            query: 用户查询
            **kwargs: 其他参数
            
        Returns:
            包含结果的字典
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "description": self.description,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools]
        }