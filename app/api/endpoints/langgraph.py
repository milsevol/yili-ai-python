from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends, status
from langgraph.prebuilt import create_react_agent
from app.agents.langgrah.wealther_agent import invoke_weather_agent

import asyncio  # 需要导入asyncio模块
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
