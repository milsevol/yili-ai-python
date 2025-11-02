from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, Union
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from app.services.langchain_service import get_langchain_client


router = APIRouter()

# ==================== Agent 基础概念示例 ====================

@router.get("/agent/what_is_agent")
async def what_is_agent():
    """
    什么是 Agent？
    
    Agent（智能代理）是一个能够自主思考、决策和执行任务的AI系统。
    与普通的聊天机器人不同，Agent 可以：
    1. 使用工具来完成复杂任务
    2. 进行多步骤推理
    3. 根据情况调整策略
    4. 记住之前的对话和操作
    
    简单来说：如果 LLM 是大脑，那么 Agent 就是有手有脚能干活的完整人。
    """
    return {
        "concept": "Agent 是能够自主行动的 AI 助手",
        "key_features": [
            "工具使用能力 - 可以调用各种API和函数",
            "推理能力 - 能够分析问题并制定解决方案", 
            "执行能力 - 能够按步骤完成复杂任务",
            "记忆能力 - 能够记住对话历史和上下文"
        ],
        "example_scenarios": [
            "帮你查天气、订机票、发邮件",
            "分析数据并生成报告",
            "自动化处理重复性工作",
            "多步骤问题解决"
        ]
    }


@router.get("/agent/simple_calculator")
async def simple_calculator_agent(question: str):
    """
    最简单的 Agent 示例：计算器助手
    
    这个例子展示了 Agent 的基本工作原理：
    1. 接收用户问题
    2. 判断是否需要使用工具
    3. 调用合适的工具
    4. 返回结果
    
    试试这些问题：
    - "帮我计算 25 + 37"
    - "100 除以 4 等于多少？"
    - "计算 2 的 8 次方"
    """
    # 获取语言模型
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义计算器工具
    @tool
    def calculator(expression: str) -> str:
        """执行数学计算，支持基本的加减乘除和幂运算"""
        try:
            # 为了安全，只允许基本的数学运算
            allowed_chars = set('0123456789+-*/().**')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return "错误：只支持基本数学运算符"
            
            result = eval(expression)
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个数学计算助手。当用户需要进行数学计算时，你要使用计算器工具。

工作流程：
1. 分析用户的问题
2. 如果涉及数学计算，使用 calculator 工具
3. 用友好的方式回答用户

注意：只有在需要计算时才使用工具，如果是简单的数学概念解释就直接回答。"""),
        ("human", "{question}")
    ])
    
    # 将工具绑定到模型
    model_with_tools = chat_model.bind_tools([calculator])
    
    # 创建消息
    messages = prompt.format_messages(question=question)
    
    # 调用模型
    response = await model_with_tools.ainvoke(messages)
    
    # 处理工具调用
    if hasattr(response, "tool_calls") and response.tool_calls:
        # 执行工具调用
        from langchain_core.messages import ToolMessage
        
        messages.append(response)
        
        for tool_call in response.tool_calls:
            if tool_call["name"] == "calculator":
                try:
                    result = calculator.invoke(tool_call["args"])
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                    messages.append(tool_message)
                except Exception as e:
                    error_message = ToolMessage(
                        content=f"计算失败：{str(e)}",
                        tool_call_id=tool_call["id"]
                    )
                    messages.append(error_message)
        
        # 获取最终回答
        final_response = await model_with_tools.ainvoke(messages)
        
        return {
            "answer": final_response.content,
            "used_calculator": True,
            "calculation": response.tool_calls[0]["args"]["expression"] if response.tool_calls else None
        }
    else:
        return {
            "answer": response.content,
            "used_calculator": False,
            "calculation": None
        }


@router.get("/agent/personal_assistant")
async def personal_assistant_agent(task: str):
    """
    个人助手 Agent：多功能助手
    
    这个助手可以帮你处理多种日常任务：
    - 获取当前时间
    - 生成随机数（比如抽奖、选择）
    - 简单的文本处理
    
    试试这些任务：
    - "现在几点了？"
    - "帮我生成一个1到10的随机数"
    - "把'hello world'转换成大写"
    - "现在几点？然后帮我生成一个幸运数字"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义多个工具
    @tool
    def get_current_time() -> str:
        """获取当前时间"""
        from datetime import datetime
        now = datetime.now()
        return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"
    
    @tool
    def generate_random_number(min_num: int = 1, max_num: int = 10) -> str:
        """生成指定范围内的随机数"""
        import random
        number = random.randint(min_num, max_num)
        return f"随机数：{number} (范围：{min_num}-{max_num})"
    
    @tool
    def text_transform(text: str, operation: str = "upper") -> str:
        """文本转换工具，支持 upper(大写)、lower(小写)、reverse(反转)"""
        if operation == "upper":
            return f"大写结果：{text.upper()}"
        elif operation == "lower":
            return f"小写结果：{text.lower()}"
        elif operation == "reverse":
            return f"反转结果：{text[::-1]}"
        else:
            return f"不支持的操作：{operation}"
    
    tools = [get_current_time, generate_random_number, text_transform]
    
    # 创建提示
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个贴心的个人助手，可以帮用户处理各种日常任务。

你有以下能力：
- get_current_time: 获取当前时间
- generate_random_number: 生成随机数
- text_transform: 文本转换（大写、小写、反转）

工作原则：
1. 仔细理解用户需求
2. 选择合适的工具来完成任务
3. 如果需要多个步骤，按顺序执行
4. 用友好的语气回复用户"""),
        ("human", "{task}")
    ])
    
    model_with_tools = chat_model.bind_tools(tools)
    messages = prompt.format_messages(task=task)
    
    # 执行任务
    response = await model_with_tools.ainvoke(messages)
    
    # 处理工具调用
    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from langchain_core.messages import ToolMessage
        
        messages.append(response)
        tool_map = {tool.name: tool for tool in tools}
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_call["args"])
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_call["args"],
                        "result": result
                    })
                    
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                    messages.append(tool_message)
                except Exception as e:
                    error_msg = f"工具执行失败：{str(e)}"
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_call["args"],
                        "result": error_msg
                    })
                    
                    error_message = ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call["id"]
                    )
                    messages.append(error_message)
        
        # 获取最终回答
        final_response = await model_with_tools.ainvoke(messages)
        
        return {
            "answer": final_response.content,
            "tools_used": tool_results
        }
    else:
        return {
            "answer": response.content,
            "tools_used": []
        }


@router.get("/agent/smart_researcher")
async def smart_researcher_agent(topic: str):
    """
    智能研究员 Agent：多步骤任务执行
    
    这个 Agent 展示了如何执行复杂的多步骤任务：
    1. 分析研究主题
    2. 制定研究计划
    3. 模拟信息收集
    4. 生成研究报告
    
    试试这些主题：
    - "人工智能的发展历史"
    - "Python编程语言的特点"
    - "可再生能源的优势"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义研究工具
    @tool
    def analyze_topic(topic: str) -> str:
        """分析研究主题，确定研究方向"""
        return f"主题分析完成：'{topic}' - 这是一个关于技术/科学领域的研究主题，需要从历史发展、现状分析、优势特点、应用场景等角度进行研究。"
    
    @tool
    def create_research_plan(topic: str) -> str:
        """为指定主题创建研究计划"""
        plan = f"""
研究计划：{topic}

1. 背景介绍 - 了解基本概念和定义
2. 历史发展 - 梳理发展时间线和重要节点  
3. 现状分析 - 分析当前发展水平和趋势
4. 特点优势 - 总结核心特征和优势
5. 应用场景 - 探讨实际应用领域
6. 未来展望 - 预测发展方向
        """
        return plan.strip()
    
    @tool
    def simulate_research(aspect: str) -> str:
        """模拟对特定方面的研究（实际应用中这里会调用真实的搜索API）"""
        research_data = {
            "背景介绍": "基础概念和定义已收集，包含核心术语解释和基本原理。",
            "历史发展": "发展时间线已整理，包含重要里程碑事件和关键人物。",
            "现状分析": "当前发展状况数据已收集，包含市场规模和技术水平。",
            "特点优势": "核心特征和竞争优势已分析，包含技术特点和应用价值。",
            "应用场景": "实际应用案例已收集，包含成功案例和应用领域。",
            "未来展望": "发展趋势预测已完成，包含技术方向和市场前景。"
        }
        return research_data.get(aspect, f"关于'{aspect}'的研究数据已收集完成。")
    
    @tool
    def generate_report(topic: str, research_data: str) -> str:
        """基于研究数据生成最终报告"""
        return f"""
# {topic} 研究报告

## 研究概述
本报告对 {topic} 进行了全面的研究分析。

## 主要发现
{research_data}

## 结论
通过深入研究，我们对 {topic} 有了全面的了解，为后续的学习和应用提供了重要参考。

## 建议
建议继续关注该领域的最新发展，并结合实际需求进行深入学习。
        """
    
    tools = [analyze_topic, create_research_plan, simulate_research, generate_report]
    
    # 创建研究员提示
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的研究员，擅长进行系统性的研究工作。

你的工作流程：
1. 使用 analyze_topic 分析研究主题
2. 使用 create_research_plan 制定研究计划  
3. 使用 simulate_research 收集各个方面的信息
4. 使用 generate_report 生成最终报告

重要提示：
- 按照逻辑顺序执行每个步骤
- 每个步骤都要使用对应的工具
- 确保研究的全面性和系统性"""),
        ("human", "请对'{topic}'进行全面研究")
    ])
    
    model_with_tools = chat_model.bind_tools(tools)
    
    # 开始研究流程
    messages = prompt.format_messages(topic=topic)
    research_steps = []
    
    # 执行多轮对话来完成研究
    for step in range(6):  # 最多6个步骤
        response = await model_with_tools.ainvoke(messages)
        
        if hasattr(response, "tool_calls") and response.tool_calls:
            from langchain_core.messages import ToolMessage
            
            messages.append(response)
            tool_map = {tool.name: tool for tool in tools}
            
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                if tool_name in tool_map:
                    try:
                        result = tool_map[tool_name].invoke(tool_call["args"])
                        research_steps.append({
                            "step": step + 1,
                            "tool": tool_name,
                            "args": tool_call["args"],
                            "result": result
                        })
                        
                        tool_message = ToolMessage(
                            content=result,
                            tool_call_id=tool_call["id"]
                        )
                        messages.append(tool_message)
                    except Exception as e:
                        error_msg = f"步骤执行失败：{str(e)}"
                        research_steps.append({
                            "step": step + 1,
                            "tool": tool_name,
                            "args": tool_call["args"],
                            "result": error_msg
                        })
            
            # 继续下一步
            continue_response = await model_with_tools.ainvoke(messages)
            messages.append(continue_response)
            
            # 如果没有更多工具调用，说明研究完成
            if not (hasattr(continue_response, "tool_calls") and continue_response.tool_calls):
                final_answer = continue_response.content
                break
        else:
            final_answer = response.content
            break
    else:
        final_answer = "研究流程已完成，请查看各步骤的详细结果。"
    
    return {
        "research_topic": topic,
        "final_report": final_answer,
        "research_steps": research_steps,
        "total_steps": len(research_steps)
    }


# 全局内存存储（实际应用中应该使用数据库）
MEMORY_STORE = {}

@router.get("/agent/memory_assistant")
async def memory_assistant_agent(
    message: str,
    conversation_id: str = Query("default", description="对话ID，用于区分不同的对话会话")
):
    """
    记忆助手 Agent：具有记忆功能的对话
    
    这个 Agent 展示了如何实现记忆功能：
    - 记住用户的偏好和信息
    - 在对话中引用之前的内容
    - 提供个性化的服务
    
    试试连续对话：
    1. "我叫张三，我喜欢编程"
    2. "我的爱好是什么？"
    3. "推荐一些适合我的书籍"
    
    注意：使用相同的 conversation_id 来保持对话连续性
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义记忆工具
    @tool
    def save_user_info(key: str, value: str, conversation_id: str = "default") -> str:
        """保存用户信息到记忆中"""
        if conversation_id not in MEMORY_STORE:
            MEMORY_STORE[conversation_id] = {}
        
        MEMORY_STORE[conversation_id][key] = value
        return f"已记住：{key} = {value}"
    
    @tool
    def get_user_info(key: str, conversation_id: str = "default") -> str:
        """从记忆中获取用户信息"""
        if conversation_id in MEMORY_STORE:
            value = MEMORY_STORE[conversation_id].get(key)
            if value:
                return f"{key}: {value}"
            else:
                return f"没有找到关于 {key} 的信息"
        else:
            return "还没有保存任何信息"
    
    @tool
    def list_all_memories(conversation_id: str = "default") -> str:
        """列出所有记住的信息"""
        if conversation_id in MEMORY_STORE:
            memories = MEMORY_STORE[conversation_id]
            if memories:
                memory_list = "\n".join([f"- {k}: {v}" for k, v in memories.items()])
                return f"我记住的信息：\n{memory_list}"
            else:
                return "还没有记住任何信息"
        else:
            return "还没有记住任何信息"
    
    tools = [save_user_info, get_user_info, list_all_memories]
    
    # 创建记忆助手提示
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""你是一个具有记忆功能的智能助手，当前对话ID是：{conversation_id}

你的能力：
- save_user_info: 保存用户告诉你的重要信息（姓名、爱好、偏好等）
- get_user_info: 查询之前保存的用户信息
- list_all_memories: 查看所有记住的信息

工作原则：
1. 当用户提到个人信息时，主动保存到记忆中
2. 当需要个性化回答时，查询相关的记忆信息
3. 利用记忆信息提供更贴心的服务
4. 所有工具调用都要包含当前的 conversation_id: {conversation_id}"""),
        ("human", "{message}")
    ])
    
    model_with_tools = chat_model.bind_tools(tools)
    messages = prompt.format_messages(message=message)
    
    # 执行对话
    response = await model_with_tools.ainvoke(messages)
    
    # 处理工具调用
    memory_operations = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from langchain_core.messages import ToolMessage
        
        messages.append(response)
        tool_map = {tool.name: tool for tool in tools}
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            if tool_name in tool_map:
                try:
                    # 确保所有工具调用都包含 conversation_id
                    args = tool_call["args"].copy()
                    args["conversation_id"] = conversation_id
                    
                    result = tool_map[tool_name].invoke(args)
                    memory_operations.append({
                        "operation": tool_name,
                        "args": args,
                        "result": result
                    })
                    
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                    messages.append(tool_message)
                except Exception as e:
                    error_msg = f"记忆操作失败：{str(e)}"
                    memory_operations.append({
                        "operation": tool_name,
                        "args": tool_call["args"],
                        "result": error_msg
                    })
        
        # 获取最终回答
        final_response = await model_with_tools.ainvoke(messages)
        
        return {
            "answer": final_response.content,
            "conversation_id": conversation_id,
            "memory_operations": memory_operations,
            "current_memories": MEMORY_STORE.get(conversation_id, {})
        }
    else:
        return {
            "answer": response.content,
            "conversation_id": conversation_id,
            "memory_operations": [],
            "current_memories": MEMORY_STORE.get(conversation_id, {})
        }


@router.get("/agent/compare_with_llm")
async def compare_with_llm(question: str):
    """
    Agent vs LLM 对比示例
    
    这个接口同时展示普通 LLM 和 Agent 的回答，
    让你直观地看到两者的区别：
    
    - LLM：只能基于训练数据回答，无法获取实时信息
    - Agent：可以使用工具获取实时信息，执行具体操作
    
    试试这些问题：
    - "现在几点了？"
    - "帮我生成一个随机密码"
    - "计算 123 * 456"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 1. 普通 LLM 回答
    llm_response = await chat_model.ainvoke(f"用户问题：{question}")
    
    # 2. Agent 回答（带工具）
    @tool
    def get_current_time() -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    
    @tool
    def generate_password(length: int = 8) -> str:
        """生成随机密码"""
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(length))
        return f"生成的密码：{password}"
    
    @tool
    def calculator(expression: str) -> str:
        """计算数学表达式"""
        try:
            result = eval(expression)
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    tools = [get_current_time, generate_password, calculator]
    
    # Agent 提示
    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能助手，可以使用工具来回答用户问题。

可用工具：
- get_current_time: 获取当前时间
- generate_password: 生成随机密码  
- calculator: 进行数学计算

如果问题需要实时信息或计算，请使用相应的工具。"""),
        ("human", "{question}")
    ])
    
    model_with_tools = chat_model.bind_tools(tools)
    agent_messages = agent_prompt.format_messages(question=question)
    agent_response = await model_with_tools.ainvoke(agent_messages)
    
    # 处理 Agent 的工具调用
    agent_final_answer = agent_response.content
    tools_used = []
    
    if hasattr(agent_response, "tool_calls") and agent_response.tool_calls:
        from langchain_core.messages import ToolMessage
        
        agent_messages.append(agent_response)
        tool_map = {tool.name: tool for tool in tools}
        
        for tool_call in agent_response.tool_calls:
            tool_name = tool_call["name"]
            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_call["args"])
                    tools_used.append({
                        "tool": tool_name,
                        "args": tool_call["args"],
                        "result": result
                    })
                    
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                    agent_messages.append(tool_message)
                except Exception as e:
                    tools_used.append({
                        "tool": tool_name,
                        "args": tool_call["args"],
                        "result": f"执行失败：{str(e)}"
                    })
        
        # 获取最终回答
        final_response = await model_with_tools.ainvoke(agent_messages)
        agent_final_answer = final_response.content
    
    return {
        "question": question,
        "llm_answer": {
            "response": llm_response.content,
            "capabilities": "只能基于训练数据回答，无法获取实时信息或执行操作"
        },
        "agent_answer": {
            "response": agent_final_answer,
            "tools_used": tools_used,
            "capabilities": "可以使用工具获取实时信息、执行计算、完成具体任务"
        },
        "comparison": {
            "key_differences": [
                "LLM：静态知识，无法更新",
                "Agent：动态获取信息，能力可扩展",
                "LLM：只能文本回答",
                "Agent：可以执行实际操作"
            ]
        }
    }


# ==================== 多 Agent 协作示例 ====================

@router.get("/agent/expert_consultation")
async def expert_consultation_system(question: str, domain: str = "general"):
    """
    专家咨询系统：多个专业 Agent 协作
    
    这个系统展示了如何让不同的专业 Agent 协作解决问题：
    1. 问题分析 Agent - 分析问题类型和复杂度
    2. 专家路由 Agent - 选择合适的专家
    3. 专业 Agent - 提供专业建议
    4. 总结 Agent - 整合所有建议
    
    支持的领域：
    - tech: 技术问题
    - business: 商业问题  
    - health: 健康问题
    - general: 通用问题
    
    试试这些问题：
    - "如何提高网站性能？" (domain=tech)
    - "如何制定营销策略？" (domain=business)
    - "如何保持健康的作息？" (domain=health)
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义问题分析 Agent
    @tool
    def analyze_question(question: str) -> str:
        """分析问题的类型、复杂度和所需专业领域"""
        analysis_prompt = f"""
        请分析以下问题："{question}"
        
        分析维度：
        1. 问题类型（技术、商业、健康、通用等）
        2. 复杂度（简单、中等、复杂）
        3. 需要的专业知识领域
        4. 建议的解决方案类型
        
        请以JSON格式返回分析结果。
        """
        # 这里简化处理，实际应该调用LLM
        return f"问题分析：'{question}' - 类型：{domain}，复杂度：中等，需要专业知识和实践经验"
    
    # 定义专家路由 Agent
    @tool
    def route_to_expert(question: str, domain: str) -> str:
        """根据问题类型路由到合适的专家Agent"""
        expert_mapping = {
            "tech": "技术专家Agent",
            "business": "商业专家Agent", 
            "health": "健康专家Agent",
            "general": "通用专家Agent"
        }
        selected_expert = expert_mapping.get(domain, "通用专家Agent")
        return f"路由决策：问题 '{question}' 已分配给 {selected_expert} 处理"
    
    # 定义专业 Agent
    @tool
    def tech_expert_agent(question: str) -> str:
        """技术专家Agent - 提供技术相关的专业建议"""
        return f"技术专家建议：针对 '{question}'，建议从性能优化、架构设计、最佳实践等角度考虑解决方案。"
    
    @tool
    def business_expert_agent(question: str) -> str:
        """商业专家Agent - 提供商业相关的专业建议"""
        return f"商业专家建议：针对 '{question}'，建议从市场分析、竞争策略、ROI评估等角度制定方案。"
    
    @tool
    def health_expert_agent(question: str) -> str:
        """健康专家Agent - 提供健康相关的专业建议"""
        return f"健康专家建议：针对 '{question}'，建议从科学依据、个人体质、生活习惯等角度给出建议。"
    
    @tool
    def general_expert_agent(question: str) -> str:
        """通用专家Agent - 提供通用建议"""
        return f"通用专家建议：针对 '{question}'，建议从多个角度综合考虑，制定平衡的解决方案。"
    
    @tool
    def summarize_consultation(question: str, expert_advice: str, analysis: str) -> str:
        """总结Agent - 整合所有专家建议"""
        return f"""
专家咨询总结报告：

问题：{question}
{analysis}

专家建议：
{expert_advice}

综合建议：
基于专家分析，建议采用系统性方法解决问题，结合理论知识和实践经验，制定可行的实施方案。

后续行动：
1. 深入研究相关领域知识
2. 制定详细的实施计划
3. 定期评估和调整策略
        """
    
    # 执行多Agent协作流程
    consultation_steps = []
    
    # 步骤1：问题分析
    analysis_result = analyze_question.invoke({"question": question})
    consultation_steps.append({
        "step": 1,
        "agent": "问题分析Agent",
        "action": "分析问题",
        "result": analysis_result
    })
    
    # 步骤2：专家路由
    routing_result = route_to_expert.invoke({"question": question, "domain": domain})
    consultation_steps.append({
        "step": 2,
        "agent": "专家路由Agent", 
        "action": "选择专家",
        "result": routing_result
    })
    
    # 步骤3：专家咨询
    expert_agents = {
        "tech": tech_expert_agent,
        "business": business_expert_agent,
        "health": health_expert_agent,
        "general": general_expert_agent
    }
    
    selected_agent = expert_agents.get(domain, general_expert_agent)
    expert_advice = selected_agent.invoke({"question": question})
    consultation_steps.append({
        "step": 3,
        "agent": f"{domain.title()}专家Agent",
        "action": "提供专业建议",
        "result": expert_advice
    })
    
    # 步骤4：总结整合
    final_summary = summarize_consultation.invoke({
        "question": question,
        "expert_advice": expert_advice,
        "analysis": analysis_result
    })
    consultation_steps.append({
        "step": 4,
        "agent": "总结Agent",
        "action": "整合建议",
        "result": final_summary
    })
    
    return {
        "question": question,
        "domain": domain,
        "consultation_process": consultation_steps,
        "final_recommendation": final_summary,
        "agents_involved": ["问题分析Agent", "专家路由Agent", f"{domain.title()}专家Agent", "总结Agent"]
    }


@router.get("/agent/project_management")
async def project_management_system(project_name: str, requirements: str):
    """
    项目管理系统：复杂多 Agent 协作
    
    这个系统展示了复杂的多Agent协作场景：
    1. 需求分析 Agent - 分析项目需求
    2. 架构设计 Agent - 设计系统架构
    3. 任务分解 Agent - 分解项目任务
    4. 资源评估 Agent - 评估所需资源
    5. 风险评估 Agent - 识别项目风险
    6. 项目规划 Agent - 制定项目计划
    
    试试这些项目：
    - project_name="电商网站", requirements="需要用户注册、商品展示、购物车、支付功能"
    - project_name="移动APP", requirements="社交功能、消息推送、用户画像分析"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义各个专业Agent
    @tool
    def requirements_analyst_agent(project_name: str, requirements: str) -> str:
        """需求分析Agent"""
        return f"""
需求分析报告 - {project_name}：

原始需求：{requirements}

功能需求分析：
- 核心功能模块识别
- 用户角色定义
- 业务流程梳理
- 接口需求分析

非功能需求：
- 性能要求：支持并发用户数
- 安全要求：数据加密、用户认证
- 可用性要求：系统稳定性
- 扩展性要求：未来功能扩展
        """
    
    @tool
    def architecture_designer_agent(project_name: str, requirements_analysis: str) -> str:
        """架构设计Agent"""
        return f"""
系统架构设计 - {project_name}：

基于需求分析：{requirements_analysis[:100]}...

推荐架构：
- 前端：React/Vue.js 单页应用
- 后端：微服务架构 (FastAPI/Django)
- 数据库：PostgreSQL + Redis缓存
- 部署：Docker + Kubernetes
- 监控：Prometheus + Grafana

架构优势：
- 高可扩展性
- 服务解耦
- 易于维护
- 支持高并发
        """
    
    @tool
    def task_decomposer_agent(project_name: str, architecture: str) -> str:
        """任务分解Agent"""
        return f"""
任务分解计划 - {project_name}：

基于架构设计：{architecture[:100]}...

主要任务模块：
1. 前端开发 (4周)
   - UI/UX设计
   - 组件开发
   - 页面集成
   
2. 后端开发 (6周)
   - API设计
   - 数据库设计
   - 业务逻辑实现
   
3. 测试阶段 (2周)
   - 单元测试
   - 集成测试
   - 性能测试
   
4. 部署上线 (1周)
   - 环境配置
   - 数据迁移
   - 监控配置
        """
    
    @tool
    def resource_estimator_agent(project_name: str, tasks: str) -> str:
        """资源评估Agent"""
        return f"""
资源评估报告 - {project_name}：

基于任务分解：{tasks[:100]}...

人力资源需求：
- 前端开发工程师：2人
- 后端开发工程师：3人
- UI/UX设计师：1人
- 测试工程师：1人
- DevOps工程师：1人

技术资源需求：
- 开发环境：云服务器 x 3
- 测试环境：云服务器 x 2
- 生产环境：云服务器 x 5
- 第三方服务：支付接口、短信服务

预算估算：
- 人力成本：约50万/3个月
- 基础设施：约5万/年
- 第三方服务：约2万/年
        """
    
    @tool
    def risk_assessor_agent(project_name: str, project_info: str) -> str:
        """风险评估Agent"""
        return f"""
风险评估报告 - {project_name}：

项目信息：{project_info[:100]}...

主要风险识别：

技术风险 (中等)：
- 新技术栈学习成本
- 第三方服务依赖
- 性能瓶颈风险

进度风险 (高)：
- 需求变更频繁
- 人员流动风险
- 技术难点预估不足

质量风险 (中等)：
- 测试覆盖不足
- 代码质量控制
- 用户体验问题

风险缓解措施：
- 技术预研和原型验证
- 敏捷开发，迭代交付
- 完善的测试策略
- 定期风险评估会议
        """
    
    @tool
    def project_planner_agent(project_name: str, all_analysis: str) -> str:
        """项目规划Agent"""
        return f"""
项目执行计划 - {project_name}：

综合分析结果：{all_analysis[:200]}...

项目里程碑：
第1阶段 (4周)：需求确认 + 架构设计
- 详细需求文档
- 技术架构确认
- 团队组建完成

第2阶段 (8周)：核心功能开发
- 后端API开发
- 前端核心页面
- 数据库设计实现

第3阶段 (4周)：功能完善 + 测试
- 功能测试
- 性能优化
- 安全测试

第4阶段 (2周)：部署上线
- 生产环境部署
- 数据迁移
- 监控配置

质量保证：
- 每周代码评审
- 自动化测试覆盖率 > 80%
- 性能基准测试
- 安全漏洞扫描

成功标准：
- 功能完整性 100%
- 性能指标达标
- 用户满意度 > 85%
- 按时交付
        """
    
    # 执行多Agent协作流程
    project_steps = []
    
    # 步骤1：需求分析
    requirements_analysis = requirements_analyst_agent.invoke({
        "project_name": project_name,
        "requirements": requirements
    })
    project_steps.append({
        "step": 1,
        "agent": "需求分析Agent",
        "result": requirements_analysis
    })
    
    # 步骤2：架构设计
    architecture_design = architecture_designer_agent.invoke({
        "project_name": project_name,
        "requirements_analysis": requirements_analysis
    })
    project_steps.append({
        "step": 2,
        "agent": "架构设计Agent",
        "result": architecture_design
    })
    
    # 步骤3：任务分解
    task_breakdown = task_decomposer_agent.invoke({
        "project_name": project_name,
        "architecture": architecture_design
    })
    project_steps.append({
        "step": 3,
        "agent": "任务分解Agent",
        "result": task_breakdown
    })
    
    # 步骤4：资源评估
    resource_estimation = resource_estimator_agent.invoke({
        "project_name": project_name,
        "tasks": task_breakdown
    })
    project_steps.append({
        "step": 4,
        "agent": "资源评估Agent",
        "result": resource_estimation
    })
    
    # 步骤5：风险评估
    risk_assessment = risk_assessor_agent.invoke({
        "project_name": project_name,
        "project_info": f"{requirements_analysis}\n{architecture_design}"
    })
    project_steps.append({
        "step": 5,
        "agent": "风险评估Agent",
        "result": risk_assessment
    })
    
    # 步骤6：项目规划
    project_plan = project_planner_agent.invoke({
        "project_name": project_name,
        "all_analysis": f"{requirements_analysis}\n{task_breakdown}\n{resource_estimation}\n{risk_assessment}"
    })
    project_steps.append({
        "step": 6,
        "agent": "项目规划Agent",
        "result": project_plan
    })
    
    return {
        "project_name": project_name,
        "original_requirements": requirements,
        "project_analysis": project_steps,
        "final_plan": project_plan,
        "agents_collaboration": {
            "total_agents": 6,
            "collaboration_pattern": "顺序协作 + 信息传递",
            "decision_points": ["架构选择", "资源分配", "风险缓解", "里程碑设定"]
        }
    }


@router.get("/agent/data_pipeline")
async def data_processing_pipeline(data_source: str, processing_type: str = "analysis"):
    """
    数据处理流水线：Agent 链式调用
    
    这个系统展示了Agent的链式调用模式：
    1. 数据采集 Agent → 2. 数据清洗 Agent → 3. 数据转换 Agent → 4. 数据分析 Agent → 5. 报告生成 Agent
    
    每个Agent的输出作为下一个Agent的输入，形成数据处理流水线。
    
    支持的处理类型：
    - analysis: 数据分析
    - ml: 机器学习
    - report: 报告生成
    
    试试这些数据源：
    - "用户行为日志"
    - "销售数据"
    - "网站访问统计"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 定义数据处理流水线中的各个Agent
    @tool
    def data_collector_agent(data_source: str) -> str:
        """数据采集Agent - 流水线第一步"""
        return f"""
数据采集完成：
- 数据源：{data_source}
- 采集时间：2024-01-15 10:00:00
- 数据量：10,000条记录
- 数据格式：JSON
- 数据质量：良好
- 采集状态：成功

原始数据样本：
{{"user_id": "12345", "action": "click", "timestamp": "2024-01-15T10:00:01", "page": "/product/123"}}
{{"user_id": "12346", "action": "view", "timestamp": "2024-01-15T10:00:02", "page": "/category/tech"}}
        """
    
    @tool
    def data_cleaner_agent(raw_data_info: str) -> str:
        """数据清洗Agent - 流水线第二步"""
        return f"""
数据清洗完成：
基于原始数据：{raw_data_info[:100]}...

清洗操作：
- 去除重复记录：删除了156条重复数据
- 处理缺失值：填充了89个缺失的timestamp
- 数据格式标准化：统一时间格式
- 异常值检测：标记了23个异常记录
- 数据验证：验证了所有必填字段

清洗后数据：
- 有效记录：9,844条
- 数据完整性：98.4%
- 数据一致性：99.1%
- 清洗状态：成功
        """
    
    @tool
    def data_transformer_agent(cleaned_data_info: str, processing_type: str) -> str:
        """数据转换Agent - 流水线第三步"""
        transformation_configs = {
            "analysis": "聚合统计、时间序列转换、分类编码",
            "ml": "特征工程、数据标准化、训练集分割",
            "report": "数据透视、图表数据准备、汇总计算"
        }
        
        config = transformation_configs.get(processing_type, "基础转换")
        
        return f"""
数据转换完成：
基于清洗数据：{cleaned_data_info[:100]}...
转换类型：{processing_type}

转换操作：{config}
- 创建了15个新特征
- 数据分组：按用户、时间、行为类型
- 计算指标：转化率、留存率、活跃度
- 数据格式：转换为分析友好格式

转换后数据结构：
- 用户维度数据：2,345个用户
- 行为维度数据：8种行为类型
- 时间维度数据：24小时分布
- 转换状态：成功
        """
    
    @tool
    def data_analyzer_agent(transformed_data_info: str, processing_type: str) -> str:
        """数据分析Agent - 流水线第四步"""
        analysis_methods = {
            "analysis": "描述性统计、趋势分析、相关性分析",
            "ml": "模型训练、特征重要性、预测分析",
            "report": "业务指标计算、同比环比、异常检测"
        }
        
        method = analysis_methods.get(processing_type, "基础分析")
        
        return f"""
数据分析完成：
基于转换数据：{transformed_data_info[:100]}...
分析方法：{method}

分析结果：
- 用户活跃度：平均每用户4.2次行为
- 热门页面：产品页面占比35%，分类页面占比28%
- 时间分布：高峰期在10-12点和19-21点
- 转化漏斗：浏览→点击→购买 转化率为12.3%

关键发现：
- 移动端用户占比67%，转化率更高
- 新用户首次访问后7天内的留存率为45%
- 推荐系统点击率比搜索高23%
- 分析状态：成功
        """
    
    @tool
    def report_generator_agent(analysis_results: str, data_source: str, processing_type: str) -> str:
        """报告生成Agent - 流水线第五步"""
        return f"""
# 数据处理流水线报告

## 项目概述
- 数据源：{data_source}
- 处理类型：{processing_type}
- 处理时间：2024-01-15
- 流水线状态：成功完成

## 数据处理摘要
基于分析结果：{analysis_results[:200]}...

## 核心指标
- 数据处理量：10,000 → 9,844条有效记录
- 数据质量评分：98.4/100
- 处理耗时：约15分钟
- 准确率：99.1%

## 业务洞察
1. **用户行为模式**：用户更偏好移动端访问，晚间活跃度高
2. **转化优化建议**：优化推荐算法，提升个性化体验
3. **产品改进方向**：加强移动端功能，优化页面加载速度

## 后续行动建议
- 建立实时数据监控仪表板
- 优化数据采集策略
- 实施A/B测试验证改进效果
- 定期更新分析模型

## 技术总结
数据流水线成功处理了{data_source}数据，通过5个Agent的协作完成了从采集到报告的全流程处理。
        """
    
    # 执行链式Agent调用
    pipeline_steps = []
    
    # 步骤1：数据采集
    collected_data = data_collector_agent.invoke({"data_source": data_source})
    pipeline_steps.append({
        "step": 1,
        "agent": "数据采集Agent",
        "input": f"数据源: {data_source}",
        "output": collected_data
    })
    
    # 步骤2：数据清洗（使用上一步的输出）
    cleaned_data = data_cleaner_agent.invoke({"raw_data_info": collected_data})
    pipeline_steps.append({
        "step": 2,
        "agent": "数据清洗Agent",
        "input": "原始数据信息",
        "output": cleaned_data
    })
    
    # 步骤3：数据转换（使用上一步的输出）
    transformed_data = data_transformer_agent.invoke({
        "cleaned_data_info": cleaned_data,
        "processing_type": processing_type
    })
    pipeline_steps.append({
        "step": 3,
        "agent": "数据转换Agent",
        "input": "清洗后数据信息",
        "output": transformed_data
    })
    
    # 步骤4：数据分析（使用上一步的输出）
    analysis_results = data_analyzer_agent.invoke({
        "transformed_data_info": transformed_data,
        "processing_type": processing_type
    })
    pipeline_steps.append({
        "step": 4,
        "agent": "数据分析Agent",
        "input": "转换后数据信息",
        "output": analysis_results
    })
    
    # 步骤5：报告生成（使用上一步的输出）
    final_report = report_generator_agent.invoke({
        "analysis_results": analysis_results,
        "data_source": data_source,
        "processing_type": processing_type
    })
    pipeline_steps.append({
        "step": 5,
        "agent": "报告生成Agent",
        "input": "分析结果",
        "output": final_report
    })
    
    return {
        "data_source": data_source,
        "processing_type": processing_type,
        "pipeline_execution": pipeline_steps,
        "final_report": final_report,
        "pipeline_metadata": {
            "total_steps": 5,
            "execution_pattern": "链式调用 (每个Agent的输出作为下个Agent的输入)",
            "data_flow": "采集 → 清洗 → 转换 → 分析 → 报告",
            "processing_time": "约15分钟",
            "success_rate": "100%"
        }
    }


@router.get("/agent/parallel_tasks")
async def parallel_task_processing(task_list: str):
    """
    并行任务处理：Agent 并发协作
    
    这个系统展示了Agent的并行协作模式：
    多个Agent同时处理不同的任务，最后汇总结果。
    
    适用场景：
    - 多个独立任务需要同时处理
    - 提高处理效率
    - 任务间无依赖关系
    
    任务列表格式：用逗号分隔，例如：
    - "翻译文档,数据分析,代码审查"
    - "市场调研,竞品分析,用户调研"
    - "性能测试,安全扫描,代码质量检查"
    """
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    # 解析任务列表
    tasks = [task.strip() for task in task_list.split(',')]
    
    # 定义不同类型的专业Agent
    @tool
    def translation_agent(task: str) -> str:
        """翻译Agent"""
        return f"""
翻译任务完成：{task}
- 源语言：中文
- 目标语言：英文
- 翻译质量：专业级
- 处理时间：3分钟
- 翻译准确率：98%
- 状态：完成

翻译样本：
"用户体验" → "User Experience"
"数据分析" → "Data Analysis"
        """
    
    @tool
    def data_analysis_agent(task: str) -> str:
        """数据分析Agent"""
        return f"""
数据分析任务完成：{task}
- 数据集大小：50,000条记录
- 分析维度：用户行为、时间趋势、转化率
- 使用算法：聚类分析、回归分析
- 处理时间：8分钟
- 准确率：95%
- 状态：完成

关键发现：
- 用户活跃度提升15%
- 转化率优化空间20%
- 推荐系统效果良好
        """
    
    @tool
    def code_review_agent(task: str) -> str:
        """代码审查Agent"""
        return f"""
代码审查任务完成：{task}
- 审查文件数：25个
- 代码行数：3,500行
- 发现问题：12个
- 严重程度：2个高危，5个中危，5个低危
- 处理时间：15分钟
- 状态：完成

审查结果：
- 代码质量评分：B+
- 安全漏洞：已标记2处
- 性能优化建议：3条
- 代码规范：符合团队标准
        """
    
    @tool
    def market_research_agent(task: str) -> str:
        """市场调研Agent"""
        return f"""
市场调研任务完成：{task}
- 调研范围：目标市场、竞争对手、用户需求
- 数据来源：行业报告、用户调研、竞品分析
- 样本数量：1,000个有效样本
- 处理时间：20分钟
- 状态：完成

调研结果：
- 市场规模：100亿元，年增长率15%
- 主要竞争对手：3家，市场份额分别为25%、20%、18%
- 用户痛点：价格敏感、功能需求多样化
- 机会点：移动端市场、个性化服务
        """
    
    @tool
    def competitor_analysis_agent(task: str) -> str:
        """竞品分析Agent"""
        return f"""
竞品分析任务完成：{task}
- 分析对象：5个主要竞品
- 分析维度：功能、价格、用户体验、市场策略
- 数据收集：产品试用、用户评价、公开资料
- 处理时间：25分钟
- 状态：完成

分析结果：
- 功能对比：我们在AI功能上有优势
- 价格策略：中等价位，性价比较高
- 用户体验：界面友好度需要提升
- 差异化优势：技术创新、服务质量
        """
    
    @tool
    def user_research_agent(task: str) -> str:
        """用户调研Agent"""
        return f"""
用户调研任务完成：{task}
- 调研方法：在线问卷、用户访谈、行为分析
- 参与用户：500名目标用户
- 调研周期：1周
- 处理时间：18分钟
- 状态：完成

调研发现：
- 用户满意度：78%
- 主要需求：功能简化、响应速度、个性化
- 使用习惯：移动端使用占70%
- 改进建议：优化操作流程、增加智能推荐
        """
    
    @tool
    def performance_test_agent(task: str) -> str:
        """性能测试Agent"""
        return f"""
性能测试任务完成：{task}
- 测试类型：负载测试、压力测试、稳定性测试
- 测试环境：生产环境模拟
- 并发用户：1000个虚拟用户
- 处理时间：30分钟
- 状态：完成

测试结果：
- 响应时间：平均200ms，95%请求<500ms
- 吞吐量：1000 TPS
- 错误率：0.1%
- 系统稳定性：99.9%
- 性能瓶颈：数据库查询需要优化
        """
    
    @tool
    def security_scan_agent(task: str) -> str:
        """安全扫描Agent"""
        return f"""
安全扫描任务完成：{task}
- 扫描类型：漏洞扫描、代码安全审计、配置检查
- 扫描范围：Web应用、API接口、数据库
- 扫描工具：OWASP ZAP、SonarQube、Nessus
- 处理时间：45分钟
- 状态：完成

扫描结果：
- 高危漏洞：0个
- 中危漏洞：2个（已修复建议）
- 低危漏洞：5个
- 安全评分：A-
- 合规性：符合GDPR、SOX要求
        """
    
    @tool
    def quality_check_agent(task: str) -> str:
        """代码质量检查Agent"""
        return f"""
代码质量检查任务完成：{task}
- 检查工具：SonarQube、ESLint、Pylint
- 检查范围：代码规范、复杂度、重复率、测试覆盖率
- 代码量：5,000行
- 处理时间：12分钟
- 状态：完成

质量报告：
- 代码规范：95%符合标准
- 圈复杂度：平均3.2，符合要求
- 代码重复率：2.1%，优秀
- 测试覆盖率：85%，良好
- 技术债务：低风险
        """
    
    # Agent映射表
    agent_mapping = {
        "翻译文档": translation_agent,
        "翻译": translation_agent,
        "数据分析": data_analysis_agent,
        "分析数据": data_analysis_agent,
        "代码审查": code_review_agent,
        "代码评审": code_review_agent,
        "市场调研": market_research_agent,
        "市场研究": market_research_agent,
        "竞品分析": competitor_analysis_agent,
        "竞争对手分析": competitor_analysis_agent,
        "用户调研": user_research_agent,
        "用户研究": user_research_agent,
        "性能测试": performance_test_agent,
        "性能检测": performance_test_agent,
        "安全扫描": security_scan_agent,
        "安全检查": security_scan_agent,
        "代码质量检查": quality_check_agent,
        "质量检查": quality_check_agent
    }
    
    # 模拟并行执行（实际应用中可以使用asyncio.gather或线程池）
    parallel_results = []
    
    for i, task in enumerate(tasks):
        # 根据任务名称选择合适的Agent
        selected_agent = None
        for key, agent in agent_mapping.items():
            if key in task:
                selected_agent = agent
                break
        
        # 如果没有匹配的专业Agent，使用通用Agent
        if not selected_agent:
            @tool
            def generic_agent(task: str) -> str:
                return f"""
通用任务处理完成：{task}
- 处理方式：通用流程
- 处理时间：10分钟
- 状态：完成
- 结果：任务已按标准流程处理完成
                """
            selected_agent = generic_agent
        
        # 执行任务
        result = selected_agent.invoke({"task": task})
        parallel_results.append({
            "task_id": i + 1,
            "task_name": task,
            "assigned_agent": selected_agent.__name__ if hasattr(selected_agent, '__name__') else "专业Agent",
            "execution_time": f"并行执行 - 开始时间: {i*2}秒",
            "result": result,
            "status": "completed"
        })
    
    # 汇总所有结果
    summary = f"""
# 并行任务处理总结报告

## 任务概览
- 总任务数：{len(tasks)}
- 并行处理：所有任务同时启动
- 完成状态：100%成功
- 总耗时：约{max(30, len(tasks) * 5)}分钟（并行执行）

## 任务分配
{chr(10).join([f"- {result['task_name']}: {result['assigned_agent']}" for result in parallel_results])}

## 效率对比
- 串行执行预估时间：{len(tasks) * 15}分钟
- 并行执行实际时间：{max(30, len(tasks) * 5)}分钟
- 效率提升：{round((len(tasks) * 15 - max(30, len(tasks) * 5)) / (len(tasks) * 15) * 100, 1)}%

## 质量保证
- 所有任务都由专业Agent处理
- 每个Agent都有独立的质量标准
- 结果汇总和交叉验证
    """
    
    return {
        "task_list": tasks,
        "execution_mode": "并行处理",
        "parallel_results": parallel_results,
        "execution_summary": summary,
        "performance_metrics": {
            "total_tasks": len(tasks),
            "success_rate": "100%",
            "parallel_efficiency": f"{round((len(tasks) * 15 - max(30, len(tasks) * 5)) / (len(tasks) * 15) * 100, 1)}%",
            "estimated_time_saved": f"{len(tasks) * 15 - max(30, len(tasks) * 5)}分钟"
        }
    }


# ==================== Agent 协作模式总结 ====================

@router.get("/agent/collaboration_patterns")
async def agent_collaboration_patterns():
    """
    Agent 协作模式总结
    
    总结不同的 Agent 协作模式和适用场景
    """
    return {
        "collaboration_patterns": {
            "1_简单协作": {
                "description": "多个专业Agent协作解决单一问题",
                "example": "专家咨询系统",
                "pattern": "问题分析 → 专家路由 → 专业处理 → 结果整合",
                "advantages": ["专业分工", "结果准确", "易于扩展"],
                "use_cases": ["专业咨询", "问题诊断", "决策支持"]
            },
            "2_复杂协作": {
                "description": "多个Agent按业务流程协作",
                "example": "项目管理系统",
                "pattern": "需求分析 → 架构设计 → 任务分解 → 资源评估 → 风险评估 → 项目规划",
                "advantages": ["流程完整", "考虑全面", "专业性强"],
                "use_cases": ["项目管理", "业务流程", "系统设计"]
            },
            "3_链式协作": {
                "description": "Agent按顺序处理，前一个的输出是后一个的输入",
                "example": "数据处理流水线",
                "pattern": "数据采集 → 数据清洗 → 数据转换 → 数据分析 → 报告生成",
                "advantages": ["数据流清晰", "质量可控", "易于调试"],
                "use_cases": ["数据处理", "内容生产", "质量检查"]
            },
            "4_并行协作": {
                "description": "多个Agent同时处理不同任务",
                "example": "并行任务处理",
                "pattern": "任务分发 → 并行执行 → 结果汇总",
                "advantages": ["效率高", "时间短", "资源利用充分"],
                "use_cases": ["批量处理", "多任务执行", "性能优化"]
            }
        },
        "选择建议": {
            "简单问题": "使用简单协作模式",
            "复杂业务": "使用复杂协作模式",
            "数据处理": "使用链式协作模式",
            "效率优先": "使用并行协作模式"
        },
        "实现要点": [
            "明确Agent职责边界",
            "设计清晰的接口协议",
            "处理好错误和异常",
            "考虑性能和扩展性",
            "建立监控和日志机制"
        ]
    }