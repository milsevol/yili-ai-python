"""
天气Agent - 专门处理天气相关查询的智能助手
"""

from typing import Dict, List, Any, Optional
from langchain_core.prompts import PromptTemplate

from .react_agent import ReactAgent
from ..tools.weather_tools import get_weather_tools


class WeatherAgent(ReactAgent):
    """专门处理天气查询的Agent"""
    
    def __init__(self, name: str = "WeatherAgent", description: str = "天气查询专家助手"):
        super().__init__(name, description)
        
        # 添加天气相关工具到Agent的工具列表
        self.add_tools(get_weather_tools())
        
        # 设置专门的天气查询提示词
        self._setup_weather_prompt()
        
        # 天气Agent的特定配置
        self.max_iterations = 3  # 天气查询通常不需要太多轮次
        self.verbose = True
    
    def _setup_weather_prompt(self):
        """设置天气查询专用的提示词"""
        weather_prompt = PromptTemplate.from_template("""
你是一个专业的天气查询助手，专门帮助用户获取天气信息和提供相关建议。

你有以下工具可以使用：
{tools}

请按照以下格式回答用户的天气相关问题：

Question: 用户的天气查询问题
Thought: 分析用户需要什么天气信息，选择合适的工具
Action: 选择要使用的工具，必须是以下之一: [{tool_names}]
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 现在我有了足够的信息来回答用户
Final Answer: 基于获取的天气信息，给出完整、友好的回答

专业提示：
1. 优先使用 get_current_weather 获取实时天气
2. 如果用户询问未来天气，使用 get_weather_forecast
3. 获取天气信息后，可以使用 get_weather_suggestion 提供生活建议
4. 回答要友好、详细，包含具体的天气数据和实用建议
5. 如果用户没有指定城市，请询问具体城市名称

开始！

Question: {input}
Thought:{agent_scratchpad}""")
        
        self.set_custom_prompt(weather_prompt)
    
    def get_supported_cities(self) -> List[str]:
        """获取支持查询的城市列表"""
        return ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "天津"]
    
    def get_info(self) -> Dict[str, Any]:
        """获取天气Agent的详细信息"""
        base_info = super().get_info()
        base_info.update({
            "agent_type": "WeatherAgent",
            "specialization": "天气查询和预报",
            "supported_cities": self.get_supported_cities(),
            "capabilities": [
                "实时天气查询",
                "天气预报查询", 
                "生活建议提供",
                "多城市支持"
            ],
            "usage_examples": [
                "北京今天天气怎么样？",
                "上海未来三天的天气预报",
                "广州的天气如何，今天适合穿什么？",
                "深圳明天会下雨吗？"
            ]
        })
        return base_info


# 便捷的工厂函数
def create_weather_agent() -> WeatherAgent:
    """创建一个配置好的天气Agent实例"""
    return WeatherAgent()


# 异步工厂函数
async def create_weather_agent_async() -> WeatherAgent:
    """异步创建天气Agent实例"""
    agent = WeatherAgent()
    # 可以在这里添加异步初始化逻辑
    return agent