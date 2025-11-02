"""
简单Agent实现 - 基于现有LLMService的简单工具调用Agent
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from .base_agent import BaseAgent
from ..services.llm_service import get_llm_service


class SimpleAgent(BaseAgent):
    """简单的工具调用Agent，基于现有的LLMService"""
    
    def __init__(self, name: str = "SimpleAgent", description: str = "简单的工具调用Agent"):
        super().__init__(name, description)
        self.llm_service = get_llm_service()
        self.system_prompt = """你是一个有用的AI助手。你可以使用提供的工具来帮助用户解决问题。

使用工具时请遵循以下原则：
1. 仔细分析用户的问题
2. 选择合适的工具来解决问题
3. 根据工具的结果给出清晰的回答
4. 如果需要多个步骤，请逐步执行"""
    
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        执行简单的工具调用任务
        
        Args:
            query: 用户查询
            **kwargs: 其他参数（如system_prompt, temperature等）
            
        Returns:
            包含结果的字典
        """
        try:
            # 准备消息
            messages: List[BaseMessage] = [HumanMessage(content=query)]
            
            # 获取系统提示词
            system_prompt = kwargs.get('system_prompt', self.system_prompt)
            
            # 调用LLM服务的工具调用方法
            result = await self.llm_service.invoke_with_tools(
                messages=messages,
                tools=self.tools,
                system_prompt=system_prompt,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', None)
            )
            
            return {
                "success": True,
                "result": result.get("response", ""),
                "tool_calls": result.get("tool_calls", []),
                "agent": self.name,
                "query": query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "query": query
            }
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt