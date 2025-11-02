"""
ReAct Agent实现 - 基于LangChain AgentExecutor的推理和行动Agent
"""

from typing import Dict, List, Any, Optional
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
from langchain import hub

from .base_agent import BaseAgent
from ..services.llm_service import get_llm_service


class ReactAgent(BaseAgent):
    """ReAct (Reasoning + Acting) Agent实现"""
    
    def __init__(self, name: str = "ReactAgent", description: str = "推理和行动Agent"):
        super().__init__(name, description)
        self.llm_service = get_llm_service()
        self.agent_executor: Optional[AgentExecutor] = None
        self.max_iterations = 5
        self.verbose = True
        self.custom_prompt: Optional[PromptTemplate] = None
    
    def _create_agent_executor(self) -> AgentExecutor:
        """创建AgentExecutor"""
        if not self.tools:
            raise ValueError("Agent需要至少一个工具才能工作")
        
        # 获取LLM
        llm = self.llm_service.clients.chat_model
        
        # 使用标准的ReAct提示词或自定义提示词
        if self.custom_prompt:
            prompt = self.custom_prompt
        else:
            # 使用LangChain Hub的标准ReAct提示词
            try:
                prompt = hub.pull("hwchase17/react")
            except Exception:
                # 如果无法从hub获取，使用简化的默认提示词
                # ReAct (Reasoning and Acting) 提示词模板 - 定义AI助手的推理和行动模式
                prompt = PromptTemplate.from_template("""
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

# 中文说明：
# 这是一个ReAct (推理和行动) 提示词模板，用于指导AI助手进行结构化的问题解决
# 
# 模板结构说明：
# - Question: 用户输入的问题
# - Thought: AI的思考过程，分析当前情况和下一步行动
# - Action: 选择要执行的工具/行动，必须是可用工具列表中的一个
# - Action Input: 传递给工具的输入参数
# - Observation: 工具执行后返回的结果
# - 循环: Thought→Action→Action Input→Observation 可以重复多次
# - Final Answer: 基于所有观察结果得出的最终答案
#
# 这种格式确保AI能够：
# 1. 系统性地思考问题
# 2. 合理选择和使用工具
# 3. 基于工具反馈调整策略
# 4. 提供有根据的最终答案

Question: {input}
Thought:{agent_scratchpad}""")
        
        # 创建ReAct agent
        agent = create_react_agent(
            llm=llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        return agent_executor
    
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        执行ReAct推理任务
        
        Args:
            query: 用户查询
            **kwargs: 其他参数
            
        Returns:
            包含结果的字典
        """
        try:
            # 更新配置
            self.max_iterations = kwargs.get('max_iterations', self.max_iterations)
            self.verbose = kwargs.get('verbose', self.verbose)
            
            # 创建或重新创建agent executor
            if self.agent_executor is None or kwargs.get('recreate_agent', False):
                self.agent_executor = self._create_agent_executor()
            
            # 执行agent
            result = await self.agent_executor.ainvoke({
                "input": query
            })
            
            return {
                "success": True,
                "result": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "agent": self.name,
                "query": query,
                "iterations": len(result.get("intermediate_steps", []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "query": query
            }
    
    def set_max_iterations(self, max_iterations: int):
        """设置最大迭代次数"""
        self.max_iterations = max_iterations
        self.agent_executor = None  # 重置以便重新创建
    
    def set_verbose(self, verbose: bool):
        """设置是否显示详细信息"""
        self.verbose = verbose
        self.agent_executor = None  # 重置以便重新创建
    
    def set_custom_prompt(self, prompt: PromptTemplate):
        """设置自定义提示词"""
        self.custom_prompt = prompt
        self.agent_executor = None  # 重置以便重新创建