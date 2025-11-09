from typing import Optional
import importlib

from langchain.schema import HumanMessage, SystemMessage, AIMessage

from app.services.llm_service import get_llm_service


def _resolve_vip_level_from_config(config: Optional[dict] = None) -> str:
    """
    从 config.configurable 解析 VIP 等级，返回对应的提示词前缀。
    """
    if not config:
        return ""
    vip_level = config.get("configurable", {}).get("vip_level")
    if vip_level == 2:
        return "作为尊贵的 VIP2 用户，您将获得最详尽、最专业的回答。"
    elif vip_level == 1:
        return "作为 VIP1 用户，您将获得更详细的回答。"
    elif vip_level == 0:
        return "作为普通用户，您将获得标准回答。"
    return ""


def _resolve_system_prompt_from_config(config: Optional[dict] = None) -> str:
    """
    从 config 动态构造 system_prompt。
    """
    # VIP 等级提示
    vip_prompt = _resolve_vip_level_from_config(config)

    # 默认提示
    default_prompt = "你是一个乐于助人的 AI 助理。"

    # 合并 VIP 提示
    if vip_prompt:
        return f"{vip_prompt} {default_prompt}"

    return default_prompt


async def invoke_dynamic_prompt_agent(
    question: str, config: Optional[dict] = None
) -> dict:
    """
    动态 prompt 示例（使用 LangGraph create_react_agent）：
    - 根据 `config.configurable.vip_level` 动态构建系统提示词；
    - 通过 LangGraph 预构建的 React Agent 执行，并可接受 `config`；
    - 返回 Agent 的状态字典（含 messages）。
    """
    # 使用统一的 LLMService 获取已配置的聊天模型
    service = get_llm_service()
    chat_model = service.clients.chat_model

    # 动态系统提示词（仅从 config 解析）
    system_prompt = _resolve_system_prompt_from_config(config)

    # 在函数内动态导入 create_react_agent，避免顶层导入报错
    try:
        prebuilt = importlib.import_module("langgraph.prebuilt")
        create_react_agent = getattr(prebuilt, "create_react_agent")
    except Exception as e:
        raise ImportError(
            "无法导入 langgraph.prebuilt.create_react_agent，请确认已安装 langgraph 并在当前环境可用。"
        ) from e

    # 使用 LangGraph 的预构建 React Agent（不绑定工具，仅示范动态提示词）
    dynamic_prompt_agent = create_react_agent(model=chat_model, tools=[])
    state = dynamic_prompt_agent.invoke(
        {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=question),
            ]
        },
        config=config,
    )
    return state


__all__ = ["invoke_dynamic_prompt_agent"]