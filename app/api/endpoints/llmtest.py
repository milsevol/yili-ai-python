from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, Union
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query


router = APIRouter()

# ==================== 基础示例 ====================

@router.get("/llm/basic")
async def llm_basic(question: str):
    """
    基础示例：直接调用语言模型
    
    这是最简单的LangChain使用方式，直接将问题发送给语言模型并返回结果
    - 获取LangChain客户端
    - 获取聊天模型
    - 异步调用模型
    - 返回内容
    """
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    # 异步调用模型并获取响应
    response = await chat_model.ainvoke(question)
    # 返回响应内容
    return response.content


@router.get("/llm/streaming")
async def llm_streaming(question: str):
    """
    流式响应示例：实时返回语言模型的输出
    
    这个示例展示如何使用流式API获取实时响应：
    - 获取LangChain客户端
    - 获取聊天模型
    - 创建异步生成器函数
    - 使用StreamingResponse返回流式内容
    """
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 创建异步生成器函数，用于流式返回结果
    async def generate_tokens():
        # 使用stream方法获取流式响应
        for response in chat_model.stream(question):
            if hasattr(response, 'content'):
                # 如果响应有content属性，返回内容
                yield response.content
            else:
                # 否则将响应转换为字符串
                yield str(response)
    
    # 使用StreamingResponse返回流式内容
    return StreamingResponse(generate_tokens(), media_type="text/plain")


@router.get("/llm/prompt_template")
async def llm_prompt_template(question: str, context: str = Query(None, description="可选的上下文信息")):
    """
    提示模板示例：使用模板构建提示
    
    这个示例展示如何使用提示模板来构建更结构化的提示：
    - 创建提示模板
    - 使用模板格式化输入
    - 调用语言模型
    - 返回结果
    """
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 创建提示模板
    if context:
        # 如果有上下文，使用包含上下文的模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有帮助的AI助手。请基于以下上下文回答问题。\n上下文: {context}"),
            ("human", "{question}")
        ])
        # 使用模板格式化输入
        chain = prompt | chat_model
        # 调用链并传入参数
        response = await chain.ainvoke({"context": context, "question": question})
    else:
        # 如果没有上下文，使用简单模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有帮助的AI助手。"),
            ("human", "{question}")
        ])
        # 使用模板格式化输入
        chain = prompt | chat_model
        # 调用链并传入参数
        response = await chain.ainvoke({"question": question})
    
    # 返回响应内容
    return response.content


@router.get("/llm/chain")
async def llm_chain(question: str):
    """
    链式操作示例：使用输出解析器处理模型输出
    
    这个示例展示如何使用链式操作和输出解析器：
    - 创建字符串输出解析器
    - 构建链式操作
    - 调用链并返回结果
    """
    # 创建字符串输出解析器
    parser = StrOutputParser()
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 构建链式操作：模型输出通过解析器处理
    chain = chat_model | parser
    
    # 调用链并获取响应
    response = await chain.ainvoke(question)
    
    # 返回处理后的响应
    return response


# ==================== 高级示例 ====================

# 定义结构化输出模型
class MovieReview(BaseModel):
    """电影评论结构化输出模型"""
    movie_name: str = Field(description="电影名称")
    rating: int = Field(description="评分(1-10)")
    review_summary: str = Field(description="评论摘要")
    pros: List[str] = Field(description="优点列表")
    cons: List[str] = Field(description="缺点列表")


@router.get("/llm/structured_output")
async def llm_structured_output(movie: str):
    """
    结构化输出示例：将模型输出解析为结构化数据
    
    这个示例展示如何使用Pydantic模型和JSON输出解析器：
    - 定义输出模型结构
    - 创建JSON输出解析器
    - 构建提示模板
    - 创建链式操作
    - 返回结构化数据
    """
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 创建JSON输出解析器，指定输出模型
    parser = JsonOutputParser(pydantic_object=MovieReview)
    
    # 构建提示模板，包含格式说明
    format_instructions = parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个电影评论专家。请对用户提到的电影进行评价，并按照指定格式输出。"),
        ("human", "请评价电影《{movie}》并提供详细分析。\n\n输出格式说明：\n你需要输出一个JSON对象，包含以下字段：\n- movie_name: 电影名称\n- rating: 评分(1-10)\n- review_summary: 评论摘要\n- pros: 优点列表\n- cons: 缺点列表")
    ])
    
    # 创建链式操作：提示模板 -> 模型 -> 解析器
    chain = prompt | chat_model | parser
    
    # 调用链并获取结构化响应
    try:
        response = await chain.ainvoke({"movie": movie})
        return response
    except Exception as e:
        # 如果解析失败，返回错误信息
        return {"error": f"无法解析响应: {str(e)}"}


@router.get("/llm/chat_history")
async def llm_chat_history(
    question: str,
    history: Optional[str] = Query(None, description="聊天历史，格式为JSON字符串，包含角色和内容")
):
    """
    聊天历史示例：使用聊天历史进行对话
    
    这个示例展示如何使用聊天历史进行连续对话：
    - 解析聊天历史
    - 构建消息列表
    - 调用语言模型
    - 返回响应和更新后的历史
    """
    import json
    
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 初始化消息列表，使用List类型注解确保可以接受不同类型的消息
    messages: List[Union[SystemMessage, HumanMessage, AIMessage]] = [
        SystemMessage(content="你是一个有帮助的AI助手，能够记住对话历史并提供连贯的回答。")
    ]
    
    # 如果有聊天历史，解析并添加到消息列表
    if history:
        try:
            history_messages = json.loads(history)
            for msg in history_messages:
                if msg["role"] == "human":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))
        except json.JSONDecodeError:
            return {"error": "聊天历史格式无效"}
    
    # 添加当前问题
    messages.append(HumanMessage(content=question))
    
    # 调用模型获取响应
    response = await chat_model.ainvoke(messages)
    
    # 更新历史，添加当前问题和回答
    new_history = []
    if history:
        try:
            new_history = json.loads(history)
        except json.JSONDecodeError:
            new_history = []
    
    new_history.append({"role": "human", "content": question})
    new_history.append({"role": "ai", "content": response.content})
    
    # 返回响应和更新后的历史
    return {
        "response": response.content,
        "history": new_history
    }


@router.get("/llm/rag_simple")
async def llm_rag_simple(question: str):
    """
    简单RAG示例：检索增强生成
    
    这个示例展示如何使用检索增强生成(RAG)：
    - 将自然语言转换为ES查询
    - 获取相关文档
    - 构建包含检索结果的提示
    - 调用语言模型生成回答
    """
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    try:
        # 将自然语言转换为ES查询
        es_query = await convert_nl_to_es_query(question, client)
        
        # 这里应该有一个实际的ES查询来获取相关文档
        # 为了示例，我们模拟一些检索结果
        retrieved_docs = [
            "这是第一个相关文档的内容。",
            "这是第二个相关文档的内容。",
            "这是第三个相关文档的内容。"
        ]
        
        # 构建包含检索结果的提示
        context = "\n\n".join(retrieved_docs)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个有帮助的AI助手。请基于以下检索到的文档回答问题。\n\n检索文档:\n{context}"),
            ("human", "{question}")
        ])
        
        # 创建链式操作
        chain = prompt | chat_model | StrOutputParser()
        
        # 调用链并获取响应
        response = await chain.ainvoke({
            "context": context,
            "question": question
        })
        
        return {
            "response": response,
            "retrieved_docs": retrieved_docs,
            "es_query": es_query
        }
    except Exception as e:
        return {"error": f"RAG处理失败: {str(e)}"}


@router.get("/llm/tool_use")
async def llm_tool_use(question: str):
    """
    工具使用示例：让模型使用工具
    
    这个示例展示如何让语言模型使用工具：
    - 定义工具函数
    - 创建提示模板
    - 调用模型并处理工具使用
    """
    from langchain_core.tools import tool
    
    # 获取LangChain客户端
    client = get_langchain_client()
    # 获取聊天模型
    chat_model = client["chat_model"]
    
    # 定义工具函数
    @tool
    def calculator(expression: str) -> str:
        """计算数学表达式的结果"""
        try:
            # 安全地评估表达式
            # 注意：在实际应用中应使用更安全的方法
            return str(eval(expression))
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    @tool
    def current_date() -> str:
        """获取当前日期和时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建工具列表
    tools = [calculator, current_date]
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有帮助的AI助手，可以使用提供的工具来回答问题。"),
        ("human", "{question}")
    ])
    
    # 将工具绑定到模型上
    model_with_tools = chat_model.bind_tools(tools)
    
    # 使用工具调用模型
    messages = prompt.format_messages(question=question)
    response = await model_with_tools.ainvoke(messages)
    
    # 检查是否有工具调用需要执行
    if hasattr(response, "tool_calls") and response.tool_calls:
        # 创建工具映射，方便根据名称查找工具
        tool_map = {tool.name: tool for tool in tools}
        
        # 执行所有工具调用
        from langchain_core.messages import ToolMessage
        
        # 将原始消息和模型响应添加到消息历史中
        messages.append(response)
        
        # 执行每个工具调用并收集结果
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            # 查找并执行工具
            if tool_name in tool_map:
                try:
                    # 执行工具函数
                    tool_result = tool_map[tool_name].invoke(tool_args)
                    # 创建工具消息并添加到消息历史
                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_id
                    )
                    messages.append(tool_message)
                except Exception as e:
                    # 如果工具执行失败，添加错误消息
                    error_message = ToolMessage(
                        content=f"工具执行错误: {str(e)}",
                        tool_call_id=tool_id
                    )
                    messages.append(error_message)
        
        # 再次调用模型，让它基于工具结果生成最终答案
        final_response = await model_with_tools.ainvoke(messages)
        
        # 返回最终响应
        return {
            "response": final_response.content,
            "tool_calls": [
                {
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "id": tool_call.get("id", ""),
                    "result": str(tool_map[tool_call["name"]].invoke(tool_call["args"])) if tool_call["name"] in tool_map else "执行失败"
                }
                for tool_call in response.tool_calls
            ]
        }
    else:
        # 如果没有工具调用，直接返回模型响应
        return {
            "response": response.content,
            "tool_calls": []
        }