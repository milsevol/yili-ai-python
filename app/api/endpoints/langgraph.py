from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends, status
from fastapi.responses import StreamingResponse
from app.agents.langgrah.wealther_agent import weather_agent, invoke_weather_agent, stream_weather_agent
from app.agents.langgrah.config_agent import invoke_dynamic_prompt_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from typing import cast, Optional
import json
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

    # 如果 vip_level 存在，则构建 cfg
    cfg = {"metadata": {"vip_level": vip_level}} if vip_level is not None else None

    state = await invoke_dynamic_prompt_agent(question=question, cfg=cfg)
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
