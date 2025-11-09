from typing import Optional

from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from app.services.llm_service import get_llm_service


def _resolve_vip_level_from_cfg(cfg: Optional[dict] = None) -> str:
    """
    从 cfg 解析 VIP 等级，返回对应的提示词前缀.
    """
    if not cfg or "metadata" not in cfg:
        return ""

    vip_level = cfg.get("metadata", {}).get("vip_level")
    if vip_level == 2:
        return "作为尊贵的 VIP2 用户，您将获得最详尽、最专业的回答。"
    elif vip_level == 1:
        return "作为 VIP1 用户，您将获得更详细的回答。"
    elif vip_level == 0:
        return "作为普通用户，您将获得标准回答。"
    return ""


def _resolve_system_prompt_from_cfg(cfg: Optional[dict] = None) -> str:
    """
    从 cfg 动态构造 system_prompt.
    """
    # VIP 等级提示
    vip_prompt = _resolve_vip_level_from_cfg(cfg)

    # 默认提示
    default_prompt = "你是一个乐于助人的 AI 助理。"

    # 合并 VIP 提示
    if vip_prompt:
        return f"{vip_prompt} {default_prompt}"

    return default_prompt


async def invoke_dynamic_prompt_agent(
    question: str, cfg: Optional[dict] = None
) -> dict:
    """
    动态 prompt 示例（独立实现，不依赖 weather_agent）：
    - 根据 `cfg` 内的参数动态构建系统提示词；
    - 使用通用 LLMService 调用聊天模型；
    - 返回包含 System/Human/AI 消息的状态字典。
    注意：cfg 可为 dict 或 RunnableConfig；可从 metadata.system_prompt/role/domain/style 等生成提示词。
    """
    service = get_llm_service()
    system_prompt = _resolve_system_prompt_from_cfg(cfg)
    message_list = [SystemMessage(content=system_prompt), HumanMessage(content=question)]

    # 调用模型获取响应文本
    ai_text = await service.invoke_chat(messages=message_list)

    # 组装返回的消息序列
    state = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
            AIMessage(content=ai_text),
        ]
    }
    return state


__all__ = ["invoke_dynamic_prompt_agent"]