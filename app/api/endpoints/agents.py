"""
Agent API端点 - 入门学习示例

这个文件展示了如何使用不同类型的Agent，每个Agent都有独立的端点和模型：
- SimpleAgent: 最简单的工具调用Agent
- ReactAgent: 会思考和推理的Agent  
- WeatherAgent: 专门查询天气的Agent

每个Agent的实现都是独立的，便于理解和学习
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.agents import SimpleAgent, ReactAgent
from app.agents.weather_agent import WeatherAgent
from app.tools import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

router = APIRouter()


# === SimpleAgent 相关模型 ===
class SimpleAgentRequest(BaseModel):
    """简单Agent请求"""
    query: str


class SimpleAgentResponse(BaseModel):
    """简单Agent响应"""
    success: bool
    result: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# === ReactAgent 相关模型 ===
class ReactAgentRequest(BaseModel):
    """推理Agent请求"""
    query: str
    max_iterations: Optional[int] = 3
    verbose: Optional[bool] = False


class ReactAgentResponse(BaseModel):
    """推理Agent响应"""
    success: bool
    result: Optional[str] = None
    iterations: Optional[int] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# === WeatherAgent 相关模型 ===
class WeatherAgentRequest(BaseModel):
    """天气Agent请求"""
    query: str


class WeatherAgentResponse(BaseModel):
    """天气Agent响应"""
    success: bool
    result: Optional[str] = None
    weather_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# === 通用模型 ===
class AgentListResponse(BaseModel):
    """Agent列表响应"""
    available_agents: List[str]
    available_tools: List[str]
    description: str


@router.get("/agents", response_model=AgentListResponse)
async def list_agents():
    """
    获取可用的Agent类型 - 入门指南
    
    这个接口告诉你有哪些Agent可以使用，
    以及每个Agent能调用哪些工具
    """
    try:
        return AgentListResponse(
            available_agents=["simple", "react", "weather"],
            available_tools=[tool.name for tool in AVAILABLE_TOOLS],
            description="可用的Agent类型：simple(简单工具调用), react(推理和行动), weather(天气查询专家)"
        )
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Agent列表失败: {str(e)}")


@router.post("/agents/simple", response_model=SimpleAgentResponse)
async def simple_agent_chat(request: SimpleAgentRequest):
    """
    SimpleAgent - 最简单的工具调用示例
    
    这个Agent会直接调用工具来回答问题，
    适合理解基本的工具调用机制
    
    示例查询：
    - "现在几点了？"
    - "计算 2+3*4"
    - "1+1等于多少？"
    """
    try:
        # 创建SimpleAgent
        agent = SimpleAgent(
            name="简单助手",
            description="简单的工具调用助手"
        )
        
        # 添加工具
        agent.add_tools(AVAILABLE_TOOLS)
        
        # 执行查询
        result = await agent.run(request.query)
        
        # 构建响应
        if result["success"]:
            return SimpleAgentResponse(
                success=True,
                result=result["result"],
                tool_calls=result.get("tool_calls")
            )
        else:
            return SimpleAgentResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error(f"SimpleAgent执行失败: {e}")
        return SimpleAgentResponse(
            success=False,
            error=f"执行失败: {str(e)}"
        )


@router.post("/agents/react", response_model=ReactAgentResponse)
async def react_agent_chat(request: ReactAgentRequest):
    """
    ReactAgent - 会思考和推理的Agent
    
    这个Agent会先思考问题，然后决定使用什么工具，
    可以进行多步推理来解决复杂问题
    
    示例查询：
    - "现在是几点，如果加上3小时是几点？"
    - "计算(2+3)*4，然后告诉我结果是奇数还是偶数"
    """
    try:
        # 创建ReactAgent
        agent = ReactAgent(
            name="推理助手",
            description="会思考推理的助手"
        )
        
        # 设置参数
        agent.set_max_iterations(request.max_iterations or 3)
        agent.set_verbose(request.verbose or False)
        
        # 添加工具
        agent.add_tools(AVAILABLE_TOOLS)
        
        # 执行查询
        result = await agent.run(request.query, verbose=request.verbose)
        
        # 构建响应
        if result["success"]:
            # 格式化中间步骤
            formatted_steps = []
            if result.get("intermediate_steps"):
                for step in result["intermediate_steps"]:
                    action, observation = step
                    formatted_steps.append({
                        "tool": action.tool,
                        "tool_input": action.tool_input,
                        "observation": str(observation)
                    })
            
            return ReactAgentResponse(
                success=True,
                result=result["result"],
                iterations=result.get("iterations", 0),
                intermediate_steps=formatted_steps,
                tool_calls=result.get("tool_calls")
            )
        else:
            return ReactAgentResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error(f"ReactAgent执行失败: {e}")
        return ReactAgentResponse(
            success=False,
            error=f"执行失败: {str(e)}"
        )


@router.post("/agents/weather", response_model=WeatherAgentResponse)
async def weather_agent_chat(request: WeatherAgentRequest):
    """
    WeatherAgent - 天气查询专家
    
    这个Agent专门处理天气相关的查询，
    已经内置了天气工具，使用起来很简单
    
    示例查询：
    - "北京今天天气怎么样？"
    - "上海明天会下雨吗？"
    - "广州适合穿什么衣服？"
    """
    try:
        # 创建WeatherAgent（已经自动包含天气工具）
        agent = WeatherAgent(
            name="天气助手",
            description="专业的天气查询助手"
        )
        
        # 执行查询
        result = await agent.run(request.query)
        
        # 构建响应
        if result["success"]:
            return WeatherAgentResponse(
                success=True,
                result=result["result"],
                weather_info=result.get("tool_calls")  # 天气信息放在这里
            )
        else:
            return WeatherAgentResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error(f"WeatherAgent执行失败: {e}")
        return WeatherAgentResponse(
            success=False,
            error=f"执行失败: {str(e)}"
        )


@router.get("/agents/weather/demo")
async def weather_demo():
    """
    天气Agent演示 - 快速体验
    
    这个端点展示了天气Agent的基本功能，
    不需要复杂的参数，直接返回示例结果
    """
    try:
        # 创建天气Agent
        agent = WeatherAgent(name="演示天气助手", description="用于演示的天气查询助手")
        
        # 执行一个示例查询
        demo_query = "北京今天天气怎么样？"
        result = await agent.run(demo_query)
        
        return {
            "demo_purpose": "展示天气Agent的基本功能",
            "example_query": demo_query,
            "agent_info": agent.get_info(),
            "result": result,
            "how_to_use": {
                "step1": "发送POST请求到 /agents/weather",
                "step2": "在请求体中包含 {'query': '你的天气问题', 'agent_name': '可选的Agent名称'}",
                "step3": "Agent会自动调用天气工具并返回结果"
            }
        }
    except Exception as e:
        logger.error(f"天气演示失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示失败: {str(e)}")


# 健康检查端点
@router.get("/agents/health")
async def health_check():
    """
    Agent服务健康检查
    """
    try:
        # 测试创建Agent
        test_agent = SimpleAgent("测试", "健康检查测试Agent")
        test_agent.add_tools(AVAILABLE_TOOLS)
        
        return {
            "status": "healthy",
            "message": "Agent服务运行正常",
            "available_tools": len(AVAILABLE_TOOLS),
            "available_agents": ["simple", "react", "weather"],
            "endpoints": {
                "simple": "/agents/simple",
                "react": "/agents/react", 
                "weather": "/agents/weather",
                "demo": "/agents/weather/demo"
            }
        }
    except Exception as e:
        logger.error(f"Agent健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"Agent服务不可用: {str(e)}")