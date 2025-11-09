from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

from ...services.llm_service import get_llm_service


@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气（演示用，返回固定文本）。

    参数：
    - city: 城市名称
    """
    return f"关于{city}，的天气一直很好!，温度25摄氏度，湿度60%"


# 使用统一的 LLMService 获取已配置好的聊天模型
_llm = get_llm_service()
_chat_model = _llm.clients.chat_model

# 系统提示词（Agent 行为准则）
SYSTEM_PROMPT = (
    "你是一个天气助手。只回答与天气相关的问题；"
    "若问题与天气无关，请礼貌说明无法回答并引导用户改问天气。"
)

# 创建一个最简的 React Agent（LangGraph 预构建）
weather_agent = create_react_agent(
    model=_chat_model,
    tools=[get_weather],
)

# 在调用时注入系统提示词
def invoke_weather_agent(user_input: str):
    return weather_agent.invoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_input),
            ]
        }
    )
__all__ = ["weather_agent", "invoke_weather_agent"]