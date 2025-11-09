from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends, status
from fastapi.responses import StreamingResponse
from app.agents.langgrah.wealther_agent import weather_agent, invoke_weather_agent, stream_weather_agent
from app.agents.langgrah.config_agent import invoke_dynamic_prompt_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import cast, Optional
import json
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import MemorySaver
from app.services.llm_service import get_llm_service
router = APIRouter()

# 基础示例 - 简单GET请求
@router.get("/langgraph/demo01")
async def demo01():
    """获取示例数据
    
    这个接口返回一个包含id和name的示例数据列表
    
    - **return**: 包含id和name的数据列表
    """
    return [
        {
            "id": "jj",
            "name": "tt"
        }
    ]

# 基础示例 - 学习例子
@router.get("/langgraph/study01")
async def study01(question: str = Query(..., description="你的天气问题或自然语言查询")):
    """LangGraph 学习示例：调用天气 Agent
    
    - 传入自然语言问题（例如："北京今天天气怎么样？"）
    - 内部通过 LangGraph React Agent + 天气工具进行推理与调用
    - 返回模型最终答案与消息轨迹
    """
    try:
        # 调用我们封装的天气 Agent（内部会注入系统提示）
        state = invoke_weather_agent(question)
        messages = state.get("messages", [])

        # 提取最终回答（通常为最后一条 AI 消息）
        final_answer = None
        if messages:
            last_msg = messages[-1]
            final_answer = getattr(last_msg, "content", None)

        # 简要序列化消息轨迹，便于在前端或调试查看
        serialized_messages = [
            {
                "type": msg.__class__.__name__,
                "content": getattr(msg, "content", "")
            }
            for msg in messages
        ]

        return {
            "success": True,
            "result": final_answer,
            "messages": serialized_messages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用天气Agent失败: {str(e)}")

def get_wealther(city: str) -> str:
    # 保留原示例函数，便于对比与学习
    return f"关于{city}, 的天气一直很好！"




@router.get("/langgraph/stream_weather")
async def stream_weather(question: str = Query(..., description="天气相关问题，演示 LangGraph 流式输出")):
    """
    流式输出示例：基于 LangGraph 预构建 React Agent 的流式调用
    - 实时返回模型产生的 AI 消息内容
    - 内部注入系统提示词以约束为天气助手
    """

    def generate():
        try:
            for chunk in stream_weather_agent(question):
                if chunk:
                    # 每个 chunk 是一段文本；按行返回，便于前端逐步显示
                    yield str(chunk)
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/langgraph/config_demo")
async def config_demo(
    question: str = Query(..., description="用户问题，如：北京的天气如何？"),
    vip_level: int = Query(None, description="可选：VIP 等级（例如 0, 1, 2）")
):
    """
    动态 prompt 示例（基于 vip_level 构建提示词）：
    - vip_level：演示基于用户等级的动态提示词。
    - 返回解析后的系统提示词、结果与消息序列。
    """

    # 如果 vip_level 存在，则构建 LangGraph 风格的 config.configurable
    config = {"configurable": {"vip_level": vip_level}} if vip_level is not None else None

    state = await invoke_dynamic_prompt_agent(question=question, config=config)
    messages = state.get("messages", [])

    return {
        "success": True,
        "system_prompt": getattr(messages[0], "content", None) if messages else None,
        "result": getattr(messages[-1], "content", None) if messages else None,
        "messages": [
            {"type": msg.__class__.__name__, "content": getattr(msg, "content", "")}
            for msg in messages
        ],
    }


# 按要求：不保留 RunnableConfig 的流式示例，保留最简非流式示例


# =============================
# Checkpointer 示例（MemorySaver）
# - 通过 thread_id 持久化对话上下文
# - 初次对话注入系统提示词；后续继续在同一线程上追加消息
# =============================

def _build_checkpointer_app():
    """构建一个最简对话图，并配置 MemorySaver 作为 checkpointer。

    图逻辑：
    - State 使用 LangGraph 预置的 MessagesState（自动 append 汇聚）
    - 单节点调用统一 LLMService 的 chat_model，并把返回消息追加到状态中
    """

    service = get_llm_service()
    chat_model = service.clients.chat_model

    def call_model(state: MessagesState):
        # 直接把已有消息喂给模型；返回的 AIMessage 追加到状态
        response = chat_model.invoke(state["messages"])  # type: ignore
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)

    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    return app


# 单例：确保 MemorySaver 在进程内复用，实现跨请求持久化
_checkpointer_app = _build_checkpointer_app()


@router.post("/langgraph/checkpointer_chat")
async def checkpointer_chat(
    thread_id: str = Body(..., embed=True, description="对话线程ID，用于持久化上下文"),
    user_input: str = Body(..., embed=True, description="用户输入的消息"),
):
    """
    基于 MemorySaver 的对话示例：
    - 传入 `thread_id` 标识对话线程；同一 ID 会持续累积上下文
    - 首次对话注入系统提示；后续只追加用户消息
    - 返回本次模型回复与当前会话的消息序列（便于调试/展示）
    """

    config = {"configurable": {"thread_id": thread_id}}

    # 查询是否已有历史，避免重复注入系统提示词
    try:
        snapshot = _checkpointer_app.get_state(config)  # type: ignore
        # 语法说明：
        # - `snapshot and ...` 是 Python 的短路与（short-circuit AND）：
        #   当 `snapshot` 为假值（如 None/False）时，右侧表达式不会执行，整体结果为假。
        # - `snapshot.values.get("messages")` 试图读取已保存的消息列表：
        #   如果该列表存在且非空，表达式为真；若不存在或为空，则为假/None。
        # - 外层 `bool(...)` 用于将上述结果明确规范成布尔值 True/False。
        has_history = bool(snapshot and snapshot.values.get("messages"))
    except Exception:
        has_history = False

    input_messages = []
    if not has_history:
        input_messages.append(SystemMessage(content="你是一个乐于助人的 AI 助理，回答简洁、准确。"))
    input_messages.append(HumanMessage(content=user_input))

    try:
        state = _checkpointer_app.invoke({"messages": input_messages}, config=config)  # type: ignore
        messages = state.get("messages", [])

        # 提取最后一条 AI 回复
        final_answer = None
        if messages:
            last_msg = messages[-1]
            final_answer = getattr(last_msg, "content", None)

        serialized_messages = [
            {"type": msg.__class__.__name__, "content": getattr(msg, "content", "")}
            for msg in messages
        ]

        return {
            "success": True,
            "thread_id": thread_id,
            "result": final_answer,
            "messages": serialized_messages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkpointer 对话调用失败: {str(e)}")


@router.get("/langgraph/checkpointer_history")
async def checkpointer_history(
    thread_id: str = Query(..., description="查询指定线程的历史对话"),
):
    """
    查看指定 `thread_id` 对话线程的历史消息。
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = _checkpointer_app.get_state(config)  # type: ignore
        if not snapshot:
            return {"success": True, "thread_id": thread_id, "messages": []}
        messages = snapshot.values.get("messages", [])
        serialized_messages = [
            {"type": msg.__class__.__name__, "content": getattr(msg, "content", "")}
            for msg in messages
        ]
        return {"success": True, "thread_id": thread_id, "messages": serialized_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取历史失败: {str(e)}")
