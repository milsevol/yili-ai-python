from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, Union
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query
from app.services.llm_service import get_llm_service, invoke_llm, stream_llm


router = APIRouter()

# ==================== 基础示例 ====================

@router.get("/llm/basic")
async def llm_basic(question: str):
    """
    基础示例：直接调用语言模型
    
    这是最简单的LangChain使用方式，直接将问题发送给语言模型并返回结果
    """
    
    # 异步调用模型并获取响应
    response = await invoke_llm(question)
    # 返回响应内容
    return response


@router.get("/llm/streaming")
async def llm_streaming(question: str):
    """
    流式响应示例：实时返回语言模型的输出
    
    这个示例展示如何使用流式API获取实时响应：
    - 使用llm_service中的stream_llm方法
    - 创建异步生成器函数
    - 使用StreamingResponse返回流式内容
    """
    
    # 创建异步生成器函数，用于流式返回结果
    async def generate_tokens():
        # 使用stream_llm方法获取流式响应
        try:
            for response in stream_llm(question):
                # 确保响应是字符串格式
                if response:
                    yield str(response)
        except Exception as e:
            yield f"Error: {str(e)}"
    
    # 使用StreamingResponse返回流式内容
    return StreamingResponse(generate_tokens(), media_type="text/plain")


@router.get("/llm/prompt_template")
async def llm_prompt_template(question: str, context: str = Query(None, description="可选的上下文信息")):
    """
    提示模板示例：使用模板构建提示
    
    这个示例展示如何使用提示模板来构建更结构化的提示：
    - 使用llm_service中的invoke_llm方法
    - 构建系统提示词和用户消息
    - 调用语言模型
    - 返回结果
    """
    
    # 构建系统提示词
    if context:
        # 如果有上下文，使用包含上下文的系统提示词
        system_prompt = f"你是一个有帮助的AI助手。请基于以下上下文回答问题。\n上下文: {context}"
    else:
        # 如果没有上下文，使用简单的系统提示词
        system_prompt = "你是一个有帮助的AI助手。"
    
    # 使用invoke_llm方法调用模型
    response = await invoke_llm(
        messages=question,
        system_prompt=system_prompt
    )
    
    # 返回响应内容
    return response


@router.get("/llm/chain")
async def llm_chain(question: str):
    """
    链式操作示例：通过 llm_service 获取模型对象进行链式操作
    
    这个示例展示如何通过 llm_service 获取底层模型对象：
    - 通过 llm_service 获取配置好的聊天模型
    - 创建字符串输出解析器
    - 构建链式操作
    - 调用链并返回结果
    
    优势：使用统一的配置管理，同时保持 LangChain 链式操作的灵活性
    """
    # 获取 llm_service 实例
    llm_service = get_llm_service()
    
    # 获取配置好的聊天模型对象
    chat_model = llm_service.clients.chat_model
    
    # 创建字符串输出解析器
    parser = StrOutputParser()
    
    # 构建链式操作：模型输出通过解析器处理
    chain = chat_model | parser
    
    # 调用链并获取响应
    response = await chain.ainvoke(question)
    
    # 返回处理后的响应
    return {
        "response": response,
        "method": "llm_service_chain",
        "model_config": {
            "temperature": llm_service.config.temperature,
            "max_tokens": llm_service.config.max_tokens,
            "timeout": llm_service.config.timeout
        }
    }


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
    结构化输出示例：通过 llm_service 实现结构化数据输出
    
    这个示例展示如何通过 llm_service 获取模型对象并使用链式操作：
    - 通过 llm_service 获取配置好的聊天模型
    - 定义输出模型结构
    - 创建JSON输出解析器
    - 构建提示模板
    - 创建链式操作
    - 返回结构化数据
    
    优势：使用统一的配置管理，同时保持结构化输出的功能
    """
    # 获取 llm_service 实例
    llm_service = get_llm_service()
    
    # 获取配置好的聊天模型对象
    chat_model = llm_service.clients.chat_model
    
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
        return {
            "data": response,
            "method": "llm_service_structured_output",
            "model_config": {
                "temperature": llm_service.config.temperature,
                "max_tokens": llm_service.config.max_tokens,
                "timeout": llm_service.config.timeout
            }
        }
    except Exception as e:
        # 如果解析失败，返回错误信息
        return {"error": f"无法解析响应: {str(e)}"}


@router.get("/llm/chat_history")
async def llm_chat_history(
    question: str,
    history: Optional[str] = Query(None, description="聊天历史，格式为JSON字符串，包含角色和内容")
):
    """
    聊天历史示例：通过 llm_service 使用聊天历史进行对话
    
    这个示例展示如何通过 llm_service 使用聊天历史进行连续对话：
    - 解析聊天历史
    - 构建消息列表
    - 直接调用 llm_service 的 invoke_chat 方法
    - 返回响应和更新后的历史
    
    优势：使用 llm_service 的统一接口，简化代码逻辑
    """
    import json
    
    # 获取 llm_service 实例
    llm_service = get_llm_service()
    
    # 初始化消息列表
    messages: List[BaseMessage] = []
    
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
    
    # 使用 llm_service 的 invoke_chat 方法，传入系统提示和消息列表
    try:
        response = await llm_service.invoke_chat(
            messages=messages,
            system_prompt="你是一个有帮助的AI助手，能够记住对话历史并提供连贯的回答。"
        )
        
        # 更新历史，添加当前问题和回答
        new_history = []
        if history:
            try:
                new_history = json.loads(history)
            except json.JSONDecodeError:
                new_history = []
        
        new_history.append({"role": "human", "content": question})
        new_history.append({"role": "ai", "content": response})
        
        # 返回AI的最新回复
        return response
        
    except Exception as e:
        return {"error": f"调用模型失败: {str(e)}"}


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
    - 使用安全的工具模块
    - 通过 llm_service 调用工具
    - 处理工具执行结果
    """
    from app.tools import AVAILABLE_TOOLS
    
    # 获取LLM服务实例
    llm_service = get_llm_service()
    
    try:
        # 使用 llm_service 的工具调用功能
        result = await llm_service.invoke_with_tools(
            messages=question,
            tools=AVAILABLE_TOOLS,
            system_prompt="你是一个有帮助的AI助手，可以使用提供的工具来回答问题。当需要进行数学计算时，请使用计算器工具。当需要获取当前时间信息时，请使用相应的时间工具。"
        )
        
        return {
            "response": result["response"],
            "tool_calls": result["tool_calls"],
            "has_tool_calls": result["has_tool_calls"],
            "message_list": result["message_list"],
            "method": "llm_service.invoke_with_tools",
            "available_tools": [tool.name for tool in AVAILABLE_TOOLS]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具调用失败: {str(e)}")


@router.get("/llm/multi_tool_demo")
async def llm_multi_tool_demo(question: str):
    """
    多工具调用演示：展示复杂的多工具协作场景
    
    这个示例专门设计来演示多工具调用的情况，包含：
    - 时间查询工具
    - 数学计算工具  
    - 天气查询工具（模拟）
    - 文本处理工具
    - 随机数生成工具
    
    示例问题：
    - "现在几点了？帮我计算一下距离2024年还有多少天，然后生成一个1-100的随机数"
    - "获取当前时间，计算2+3*4的结果，然后把结果转换为大写文本"
    - "查询今天天气，计算温度华氏度转摄氏度，生成随机推荐"
    """
    from langchain_core.tools import tool
    import random
    import json
    
    # 获取LangChain客户端
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义多个工具函数
    @tool
    def get_current_time() -> str:
        """获取当前的详细时间信息，包括日期、时间、星期等"""
        from datetime import datetime
        now = datetime.now()
        return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')} 星期{['一','二','三','四','五','六','日'][now.weekday()]}"
    
    @tool
    def advanced_calculator(expression: str) -> str:
        """高级计算器，支持复杂数学表达式计算，包括基本运算、幂运算等"""
        try:
            # 支持更多数学函数
            import math
            # 创建安全的计算环境
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": math.sqrt,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "pi": math.pi, "e": math.e
            }
            result = eval(expression, safe_dict)
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    @tool
    def weather_simulator(city: str = "北京") -> str:
        """模拟天气查询工具，返回指定城市的模拟天气信息"""
        import random
        temperatures = list(range(-10, 35))
        weather_conditions = ["晴天", "多云", "阴天", "小雨", "大雨", "雪天"]
        
        temp = random.choice(temperatures)
        condition = random.choice(weather_conditions)
        humidity = random.randint(30, 90)
        
        return f"{city}天气：{condition}，温度{temp}°C，湿度{humidity}%"
    
    @tool
    def text_processor(text: str, operation: str = "upper") -> str:
        """文本处理工具，支持多种文本操作：upper(大写)、lower(小写)、reverse(反转)、length(长度)"""
        try:
            if operation == "upper":
                return f"大写转换：{text.upper()}"
            elif operation == "lower":
                return f"小写转换：{text.lower()}"
            elif operation == "reverse":
                return f"反转文本：{text[::-1]}"
            elif operation == "length":
                return f"文本长度：{len(text)} 个字符"
            else:
                return f"不支持的操作：{operation}。支持的操作：upper, lower, reverse, length"
        except Exception as e:
            return f"文本处理错误：{str(e)}"
    
    @tool
    def random_generator(min_val: int = 1, max_val: int = 100, count: int = 1) -> str:
        """随机数生成器，可以生成指定范围内的随机数"""
        try:
            if count == 1:
                result = random.randint(min_val, max_val)
                return f"随机数：{result} (范围：{min_val}-{max_val})"
            else:
                results = [random.randint(min_val, max_val) for _ in range(count)]
                return f"随机数列表：{results} (范围：{min_val}-{max_val}，数量：{count})"
        except Exception as e:
            return f"随机数生成错误：{str(e)}"
    
    @tool
    def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
        """单位转换工具，支持温度、长度等单位转换"""
        try:
            # 温度转换
            if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
                result = (value * 9/5) + 32
                return f"温度转换：{value}°C = {result:.2f}°F"
            elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
                result = (value - 32) * 5/9
                return f"温度转换：{value}°F = {result:.2f}°C"
            # 长度转换
            elif from_unit.lower() == "meter" and to_unit.lower() == "feet":
                result = value * 3.28084
                return f"长度转换：{value}米 = {result:.2f}英尺"
            elif from_unit.lower() == "feet" and to_unit.lower() == "meter":
                result = value / 3.28084
                return f"长度转换：{value}英尺 = {result:.2f}米"
            else:
                return f"不支持的转换：{from_unit} -> {to_unit}"
        except Exception as e:
            return f"单位转换错误：{str(e)}"
    
    # 创建工具列表
    tools = [
        get_current_time, 
        advanced_calculator, 
        weather_simulator, 
        text_processor, 
        random_generator, 
        unit_converter
    ]
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能助手，拥有多种工具来帮助用户解决问题。

可用工具：
1. get_current_time - 获取当前时间
2. advanced_calculator - 高级数学计算
3. weather_simulator - 天气查询（模拟）
4. text_processor - 文本处理
5. random_generator - 随机数生成
6. unit_converter - 单位转换

重要指导原则：
- 当用户的问题包含多个任务时，你需要逐步完成每个任务
- 每次只调用完成当前步骤所需的工具
- 完成一个步骤后，继续处理下一个步骤
- 确保所有用户要求的任务都得到完成

例如，如果用户问"现在几点了？帮我计算一下2+3*4的结果，然后生成一个1-100的随机数"，你应该：
1. 首先调用 get_current_time 获取时间
2. 然后调用 advanced_calculator 计算数学表达式
3. 最后调用 random_generator 生成随机数
4. 将所有结果整合给出完整答案

请按照用户问题的逻辑顺序，逐步使用相应的工具。"""),
        ("human", "{question}")
    ])
    
    # 将工具绑定到模型上
    model_with_tools = chat_model.bind_tools(tools)
    
    # 使用工具调用模型
    messages = prompt.format_messages(question=question)
    response = await model_with_tools.ainvoke(messages)
    
    # 创建工具映射
    tool_map = {tool.name: tool for tool in tools}
    from langchain_core.messages import ToolMessage
    
    # 记录所有工具调用详情
    all_tool_calls = []
    max_iterations = 5  # 防止无限循环
    iteration = 0
    
    # 多轮工具调用循环
    while iteration < max_iterations:
        iteration += 1
        
        # 检查当前响应是否有工具调用
        if hasattr(response, "tool_calls") and response.tool_calls:
            # 将模型响应添加到消息历史
            messages.append(response)
            
            # 执行当前轮次的所有工具调用
            current_round_tools = []
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
                        
                        # 记录工具调用详情
                        tool_detail = {
                            "name": tool_name,
                            "args": tool_args,
                            "id": tool_id,
                            "result": str(tool_result),
                            "status": "success",
                            "round": iteration
                        }
                        current_round_tools.append(tool_detail)
                        all_tool_calls.append(tool_detail)
                        
                    except Exception as e:
                        # 如果工具执行失败，添加错误消息
                        error_message = ToolMessage(
                            content=f"工具执行错误: {str(e)}",
                            tool_call_id=tool_id
                        )
                        messages.append(error_message)
                        
                        # 记录错误详情
                        tool_detail = {
                            "name": tool_name,
                            "args": tool_args,
                            "id": tool_id,
                            "result": f"执行失败: {str(e)}",
                            "status": "error",
                            "round": iteration
                        }
                        current_round_tools.append(tool_detail)
                        all_tool_calls.append(tool_detail)
            
            # 再次调用模型，让它基于工具结果决定下一步
            response = await model_with_tools.ainvoke(messages)
            
            # 如果这轮没有工具调用，说明任务完成
            if not (hasattr(response, "tool_calls") and response.tool_calls):
                break
                
        else:
            # 没有工具调用，退出循环
            break
    
    # 返回详细的响应信息
    if all_tool_calls:
        return {
            "response": response.content,
            "tool_calls_count": len(all_tool_calls),
            "tool_calls": all_tool_calls,
            "execution_summary": f"在 {iteration} 轮中成功执行了 {len(all_tool_calls)} 个工具调用",
            "available_tools": [tool.name for tool in tools],
            "rounds": iteration
        }
    else:
        # 如果没有工具调用，直接返回模型响应
        return {
            "response": response.content,
            "tool_calls_count": 0,
            "tool_calls": [],
            "execution_summary": "未使用任何工具",
            "available_tools": [tool.name for tool in tools]
        }