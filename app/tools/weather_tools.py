"""
天气查询工具 - 提供天气信息查询功能
"""

import json
import asyncio
from typing import Dict, Any
from langchain.tools import tool
import aiohttp
from datetime import datetime


@tool
async def get_current_weather(city: str) -> str:
    """
    获取指定城市的当前天气信息
    
    Args:
        city: 城市名称，例如 "北京", "上海", "广州"
        
    Returns:
        包含当前天气信息的JSON字符串
    """
    try:
        # 模拟天气API调用 (实际使用时替换为真实的天气API)
        # 这里使用模拟数据，实际项目中应该调用真实的天气API如OpenWeatherMap
        
        weather_data = {
            "city": city,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": "22°C",
            "weather": "晴天",
            "humidity": "65%",
            "wind_speed": "微风 2级",
            "air_quality": "良好",
            "description": f"{city}当前天气晴朗，温度适宜"
        }
        
        # 根据城市返回不同的模拟数据
        city_weather_map = {
            "北京": {"temperature": "18°C", "weather": "多云", "humidity": "45%"},
            "上海": {"temperature": "25°C", "weather": "小雨", "humidity": "78%"},
            "广州": {"temperature": "28°C", "weather": "晴天", "humidity": "82%"},
            "深圳": {"temperature": "27°C", "weather": "阴天", "humidity": "75%"},
            "杭州": {"temperature": "23°C", "weather": "晴天", "humidity": "60%"}
        }
        
        if city in city_weather_map:
            weather_data.update(city_weather_map[city])
            weather_data["description"] = f"{city}当前{weather_data['weather']}，温度{weather_data['temperature']}"
        
        return json.dumps(weather_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"获取{city}天气信息失败: {str(e)}"


@tool
async def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    获取指定城市的天气预报
    
    Args:
        city: 城市名称
        days: 预报天数，默认3天
        
    Returns:
        包含天气预报信息的JSON字符串
    """
    try:
        # 模拟天气预报数据
        forecast_data = {
            "city": city,
            "forecast_days": days,
            "forecast": []
        }
        
        # 生成模拟的预报数据
        weather_patterns = ["晴天", "多云", "小雨", "阴天"]
        temperatures = ["20°C", "22°C", "25°C", "18°C", "27°C"]
        
        for i in range(days):
            date = datetime.now()
            date = date.replace(day=date.day + i + 1)
            
            day_forecast = {
                "date": date.strftime("%Y-%m-%d"),
                "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                "weather": weather_patterns[i % len(weather_patterns)],
                "high_temp": temperatures[i % len(temperatures)],
                "low_temp": f"{int(temperatures[i % len(temperatures)][:-2]) - 5}°C",
                "humidity": f"{60 + i * 5}%"
            }
            forecast_data["forecast"].append(day_forecast)
        
        return json.dumps(forecast_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"获取{city}天气预报失败: {str(e)}"


@tool
def get_weather_suggestion(weather_info: str) -> str:
    """
    根据天气信息提供生活建议
    
    Args:
        weather_info: 天气信息JSON字符串
        
    Returns:
        生活建议字符串
    """
    try:
        weather_data = json.loads(weather_info)
        weather = weather_data.get("weather", "")
        temperature = weather_data.get("temperature", "")
        
        suggestions = []
        
        # 根据天气给出建议
        if "雨" in weather:
            suggestions.append("🌧️ 今天有雨，记得带伞出门")
            suggestions.append("🚗 出行注意安全，路面可能湿滑")
        elif "晴" in weather:
            suggestions.append("☀️ 天气晴朗，适合户外活动")
            suggestions.append("🕶️ 阳光较强，建议佩戴太阳镜")
        elif "多云" in weather or "阴" in weather:
            suggestions.append("☁️ 天气阴沉，可能随时变天")
            suggestions.append("🧥 建议携带外套以备不时之需")
        
        # 根据温度给出建议
        if temperature:
            temp_num = int(temperature.replace("°C", ""))
            if temp_num < 10:
                suggestions.append("🧥 温度较低，注意保暖")
            elif temp_num > 30:
                suggestions.append("🌡️ 温度较高，注意防暑降温")
            elif 20 <= temp_num <= 25:
                suggestions.append("👕 温度适宜，穿着舒适")
        
        return "\n".join(suggestions) if suggestions else "天气信息正常，注意适时增减衣物"
        
    except Exception as e:
        return f"生成天气建议失败: {str(e)}"


# 获取所有天气工具的函数
def get_weather_tools():
    """返回所有天气相关的工具"""
    return [
        get_current_weather,
        get_weather_forecast,
        get_weather_suggestion
    ]