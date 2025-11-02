"""
LLM服务模块 - 提供大模型基础接口调用功能

该模块封装了大语言模型的基础调用接口，支持多种模型提供商，
提供统一的调用方式和错误处理机制。

主要功能：
1. 配置管理和API密钥读取
2. LLM客户端初始化
3. 统一的模型调用接口
4. 错误处理和重试机制
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pydantic import SecretStr
from dotenv import load_dotenv

# LangChain相关导入
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool


@dataclass
class LLMConfig:
    """LLM配置类"""
    deepseek_api_key: str
    qwen_api_key: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    timeout: int = 30


@dataclass
class LLMClients:
    """LLM客户端容器类"""
    chat_model: ChatOpenAI
    embedding_model: DashScopeEmbeddings
    config: LLMConfig


class LLMService:
    """LLM服务类 - 提供统一的大模型调用接口"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化LLM服务
        
        Args:
            config: LLM配置，如果为None则从环境变量读取
        """
        self.config = config or self._load_config()
        self.clients = self._init_clients()
    
    def _load_config(self) -> LLMConfig:
        """
        从环境变量加载配置
        
        Returns:
            LLMConfig: 配置对象
            
        Raises:
            ValueError: 当必要的API密钥未配置时
        """
        # 加载.env文件
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        load_dotenv(env_path)
        
        # 从环境变量获取API密钥
        deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
        qwen_key = os.getenv('DASHSCOPE_API_KEY', '')
        
        if not deepseek_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
        
        if not qwen_key:
            print("警告: DASHSCOPE_API_KEY 环境变量未设置，将使用DeepSeek API Key代替")
            qwen_key = deepseek_key
        
        # 处理可选的环境变量
        max_tokens_env = os.getenv('LLM_MAX_TOKENS')
        max_tokens = int(max_tokens_env) if max_tokens_env else None
        
        return LLMConfig(
            deepseek_api_key=deepseek_key,
            qwen_api_key=qwen_key,
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.0')),
            max_tokens=max_tokens,
            timeout=int(os.getenv('LLM_TIMEOUT', '30'))
        )
    
    def _init_clients(self) -> LLMClients:
        """
        初始化LLM客户端
        
        Returns:
            LLMClients: 客户端容器对象
        """
        # 创建聊天模型客户端
        chat_model_kwargs = {
            "model": "deepseek-chat",
            "api_key": SecretStr(self.config.deepseek_api_key),
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "base_url": "https://api.deepseek.com/v1"
        }
        
        # 只有当max_tokens不为None时才添加该参数
        if self.config.max_tokens is not None:
            chat_model_kwargs["max_tokens"] = self.config.max_tokens
            
        chat_model = ChatOpenAI(**chat_model_kwargs)
        
        # 创建嵌入模型客户端
        embedding_model = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key=self.config.qwen_api_key
        )
        
        return LLMClients(
            chat_model=chat_model,
            embedding_model=embedding_model,
            config=self.config
        )
    
    async def invoke_chat(
        self,
        messages: Union[str, List[BaseMessage]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用聊天模型
        
        Args:
            messages: 消息内容，可以是字符串或消息对象列表
            system_prompt: 系统提示词
            temperature: 温度参数，覆盖默认配置
            max_tokens: 最大token数，覆盖默认配置
            
        Returns:
            str: 模型返回的文本内容
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            # 构造消息列表
            message_list = []
            
            # 添加系统提示词
            if system_prompt:
                message_list.append(SystemMessage(content=system_prompt))
            
            # 处理输入消息
            if isinstance(messages, str):
                message_list.append(HumanMessage(content=messages))
            elif isinstance(messages, list):
                message_list.extend(messages)
            else:
                raise TypeError("messages 参数必须是字符串或消息对象列表")
            
            # 创建临时客户端（如果需要覆盖参数）
            chat_model = self.clients.chat_model
            if temperature is not None or max_tokens is not None:
                temp_kwargs = {
                    "model": "deepseek-chat",
                    "api_key": SecretStr(self.config.deepseek_api_key),
                    "temperature": temperature if temperature is not None else self.config.temperature,
                    "timeout": self.config.timeout,
                    "base_url": "https://api.deepseek.com/v1"
                }
                
                # 只有当max_tokens不为None时才添加该参数
                final_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
                if final_max_tokens is not None:
                    temp_kwargs["max_tokens"] = final_max_tokens
                    
                chat_model = ChatOpenAI(**temp_kwargs)
            
            # 调用模型
            result = await chat_model.ainvoke(message_list)
            return str(result.content)
            
        except Exception as e:
            print(f"LLM聊天调用失败: {str(e)}")
            raise

    def stream_chat(
        self,
        messages: Union[str, List[BaseMessage]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        流式调用聊天模型
        
        Args:
            messages: 消息内容，可以是字符串或消息对象列表
            system_prompt: 系统提示词
            temperature: 温度参数，覆盖默认配置
            max_tokens: 最大token数，覆盖默认配置
            
        Returns:
            Generator: 流式响应生成器
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            # 构造消息列表
            message_list = []
            
            # 添加系统提示词
            if system_prompt:
                message_list.append(SystemMessage(content=system_prompt))
            
            # 处理输入消息
            if isinstance(messages, str):
                message_list.append(HumanMessage(content=messages))
            elif isinstance(messages, list):
                message_list.extend(messages)
            else:
                raise TypeError("messages 参数必须是字符串或消息对象列表")
            
            # 创建临时客户端（如果需要覆盖参数）
            chat_model = self.clients.chat_model
            if temperature is not None or max_tokens is not None:
                temp_kwargs = {
                    "model": "deepseek-chat",
                    "api_key": SecretStr(self.config.deepseek_api_key),
                    "temperature": temperature if temperature is not None else self.config.temperature,
                    "timeout": self.config.timeout,
                    "base_url": "https://api.deepseek.com/v1"
                }
                
                # 只有当max_tokens不为None时才添加该参数
                final_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
                if final_max_tokens is not None:
                    temp_kwargs["max_tokens"] = final_max_tokens
                    
                chat_model = ChatOpenAI(**temp_kwargs)
            
            # 使用stream方法获取流式响应
            for response in chat_model.stream(message_list):
                if hasattr(response, 'content'):
                    yield response.content
                else:
                    yield str(response)
                    
        except Exception as e:
            print(f"LLM流式调用失败: {str(e)}")
            raise
            print(f"LLM聊天调用失败: {str(e)}")
            raise
    
    async def invoke_with_tools(
        self,
        messages: Union[str, List[BaseMessage]],
        tools: List[BaseTool],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        使用工具调用LLM
        
        Args:
            messages: 消息内容，可以是字符串或消息列表
            tools: 可用工具列表
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            Dict[str, Any]: 包含响应和工具调用信息的字典
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            # 构建消息列表
            if isinstance(messages, str):
                message_list = []
                if system_prompt:
                    message_list.append(SystemMessage(content=system_prompt))
                message_list.append(HumanMessage(content=messages))
            else:
                message_list = messages.copy()
                if system_prompt:
                    message_list.insert(0, SystemMessage(content=system_prompt))
            
            # 创建工具映射
            tool_map = {tool.name: tool for tool in tools}
            
            # 绑定工具到模型
            if temperature is not None or max_tokens is not None:
                # 创建临时客户端以覆盖参数
                temp_kwargs = {
                    "model": "deepseek-chat",
                    "api_key": self.config.deepseek_api_key,
                    "temperature": temperature if temperature is not None else self.config.temperature,
                    "timeout": self.config.timeout,
                    "base_url": "https://api.deepseek.com/v1"
                }
                
                final_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
                if final_max_tokens is not None:
                    temp_kwargs["max_tokens"] = final_max_tokens
                    
                chat_model = ChatOpenAI(**temp_kwargs)
            else:
                chat_model = self.clients.chat_model
            
            model_with_tools = chat_model.bind_tools(tools)
            
            # 初始调用
            response = await model_with_tools.ainvoke(message_list)
            
            # 检查是否有工具调用
            if hasattr(response, "tool_calls") and getattr(response, "tool_calls", None):
                # 将模型响应添加到消息历史
                message_list.append(response)
                
                # 执行工具调用
                tool_results = []
                for tool_call in getattr(response, "tool_calls", []):
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]
                    
                    if tool_name in tool_map:
                        try:
                            # 执行工具
                            tool_result = tool_map[tool_name].invoke(tool_args)
                            tool_results.append({
                                "name": tool_name,
                                "args": tool_args,
                                "id": tool_id,
                                "result": str(tool_result)
                            })
                            
                            # 添加工具消息到历史
                            tool_message = ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_id
                            )
                            message_list.append(tool_message)
                            
                        except Exception as e:
                            error_result = f"工具执行错误: {str(e)}"
                            tool_results.append({
                                "name": tool_name,
                                "args": tool_args,
                                "id": tool_id,
                                "result": error_result
                            })
                            
                            # 添加错误消息到历史
                            error_message = ToolMessage(
                                content=error_result,
                                tool_call_id=tool_id
                            )
                            message_list.append(error_message)
                
                # 再次调用模型生成最终响应
                final_response = await model_with_tools.ainvoke(message_list)
                
                return {
                    "response": final_response.content,
                    "tool_calls": tool_results,
                    "message_list": message_list,
                    "has_tool_calls": True
                }
            else:
                # 没有工具调用，直接返回响应
                return {
                    "response": response.content,
                    "tool_calls": [],
                    "has_tool_calls": False
                }
                
        except Exception as e:
            print(f"LLM工具调用失败: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            vector = await self.clients.embedding_model.aembed_query(text)
            return vector
        except Exception as e:
            print(f"嵌入向量生成失败: {str(e)}")
            raise
    
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
            
        Raises:
            Exception: 调用失败时抛出异常
        """
        try:
            vectors = await self.clients.embedding_model.aembed_documents(texts)
            return vectors
        except Exception as e:
            print(f"批量嵌入向量生成失败: {str(e)}")
            raise


# 全局服务实例（单例模式）
_llm_service_instance: Optional[LLMService] = None


def get_llm_service(config: Optional[LLMConfig] = None) -> LLMService:
    """
    获取LLM服务实例（单例模式）
    
    Args:
        config: LLM配置，仅在首次调用时生效
        
    Returns:
        LLMService: LLM服务实例
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService(config)
    return _llm_service_instance


# 便捷函数
async def invoke_llm(
    messages: Union[str, List[BaseMessage]],
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    便捷的LLM调用函数
    
    Args:
        messages: 消息内容
        system_prompt: 系统提示词
        temperature: 温度参数
        max_tokens: 最大token数
        
    Returns:
        str: 模型返回的文本内容
    """
    service = get_llm_service()
    return await service.invoke_chat(messages, system_prompt, temperature, max_tokens)


def stream_llm(
    messages: Union[str, List[BaseMessage]],
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    便捷的LLM流式调用函数
    
    Args:
        messages: 消息内容
        system_prompt: 系统提示词
        temperature: 温度参数
        max_tokens: 最大token数
        
    Returns:
        Generator: 流式响应生成器
    """
    service = get_llm_service()
    return service.stream_chat(messages, system_prompt, temperature, max_tokens)


async def generate_embedding(text: str) -> List[float]:
    """
    便捷的嵌入向量生成函数
    
    Args:
        text: 输入文本
        
    Returns:
        List[float]: 嵌入向量
    """
    service = get_llm_service()
    return await service.generate_embedding(text)


# 使用示例和测试代码
async def example_usage():
    """使用示例"""
    try:
        # 1. 简单文本调用
        response1 = await invoke_llm("你好，请介绍一下自己")
        print(f"简单调用结果: {response1}")
        
        # 2. 带系统提示词的调用
        response2 = await invoke_llm(
            "请分析这段代码的功能",
            system_prompt="你是一个专业的代码分析师，请提供详细的分析"
        )
        print(f"带系统提示词结果: {response2}")
        
        # 3. 使用消息对象列表
        messages = [
            SystemMessage(content="你是一个有用的助手"),
            HumanMessage(content="请解释什么是机器学习"),
            AIMessage(content="机器学习是人工智能的一个分支..."),
            HumanMessage(content="能举个具体例子吗？")
        ]
        response3 = await invoke_llm(messages)
        print(f"多轮对话结果: {response3}")
        
        # 4. 生成嵌入向量
        embedding = await generate_embedding("这是一段测试文本")
        print(f"嵌入向量维度: {len(embedding)}")
        
        # 5. 使用服务类实例
        service = get_llm_service()
        response4 = await service.invoke_chat(
            "请用100字总结人工智能的发展历程",
            temperature=0.7,
            max_tokens=200
        )
        print(f"服务类调用结果: {response4}")
        
    except Exception as e:
        print(f"示例执行失败: {str(e)}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())