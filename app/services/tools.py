"""
Tools Module - Dynamic function calls for agents
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
import json
from math import *

from langchain.tools import Tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class WeatherTool:
    """Tool for getting weather information"""
    
    def __init__(self):
        """Initialize weather tool"""
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "http://api.weatherapi.com/v1"
        
        if not self.api_key:
            logger.warning("WEATHER_API_KEY not set in environment variables")
    
    def get_weather(self, location: str = "Dhaka") -> str:
        """
        Get current weather for a location
        
        Args:
            location: City name or coordinates
            
        Returns:
            Weather information as string
        """
        try:
            if not self.api_key:
                return "Weather API key not configured. Please set WEATHER_API_KEY in your .env file."
            
            # Make API request
            url = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "yes"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                return "Invalid Weather API key. Please check your WEATHER_API_KEY in .env file."
            elif response.status_code == 400:
                return f"Location '{location}' not found. Please provide a valid city name."
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            current = data.get("current", {})
            location_data = data.get("location", {})
            
            # Format response
            response_text = f"""Current weather in {location_data.get('name')}, {location_data.get('country')}:
                • Temperature: {current.get('temp_c')}°C ({current.get('temp_f')}°F)
                • Feels like: {current.get('feelslike_c')}°C
                • Condition: {current.get('condition', {}).get('text')}
                • Humidity: {current.get('humidity')}%
                • Wind: {current.get('wind_kph')} km/h
                • UV Index: {current.get('uv')}"""
            
            logger.info(f"Successfully retrieved weather for {location}")
            return response_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return f"Unable to fetch weather data. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error in get_weather: {str(e)}")
            return f"Error getting weather information. Please try again."
    
    def get_forecast(self, location: str = "Dhaka", days: int = 3) -> str:
        """
        Get weather forecast for a location
        
        Args:
            location: City name or coordinates
            days: Number of days (1-10)
            
        Returns:
            Weather forecast as string
        """
        try:
            if not self.api_key:
                return "Weather API key not configured."
            
            # Limit days to API maximum
            days = min(days, 10)
            
            # Make API request
            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": days,
                "aqi": "yes"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract forecast information
            location_data = data.get("location", {})
            forecast_days = data.get("forecast", {}).get("forecastday", [])
            
            forecast_text = f"Weather Forecast for {location_data.get('name')}, {location_data.get('country')}:\n\n"
            
            for day in forecast_days:
                date = day.get("date")
                day_data = day.get("day", {})
                
                forecast_text += f"""
                    {date}:
                    - Max Temp: {day_data.get('maxtemp_c')}°C / Min Temp: {day_data.get('mintemp_c')}°C
                    - Condition: {day_data.get('condition', {}).get('text')}
                    - Chance of Rain: {day_data.get('daily_chance_of_rain')}%
                    - Max Wind: {day_data.get('maxwind_kph')} km/h
                    """
            
            logger.info(f"Successfully retrieved {days}-day forecast for {location}")
            return forecast_text
            
        except Exception as e:
            logger.error(f"Error getting forecast: {str(e)}")
            return f"Error getting weather forecast: {str(e)}"
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="weather",
            func=self.get_weather,
            description="Get current weather information for any location. Input should be a city name."
        )

class CalculatorTool:
    """Tool for mathematical calculations"""
    
    def calculate(self, expression: str) -> str:
        """
        Perform mathematical calculations
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Calculation result as string
        """
        try:
            # Safe evaluation of mathematical expressions
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": sqrt,
                "sin": sin, "cos": cos, "tan": tan,
                "log": log, "log10": log10, "exp": exp,
                "pi": pi, "e": e
            }
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            logger.info(f"Calculated: {expression} = {result}")
            return f"Result: {result}"
            
        except Exception as e:
            logger.error(f"Error in calculation: {str(e)}")
            return f"Error performing calculation: {str(e)}"
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="calculator",
            func=self.calculate,
            description="Perform mathematical calculations. Input should be a valid mathematical expression."
        )

class TimezoneTool:
    """Tool for timezone and time-related operations"""
    
    def get_current_time(self, timezone: str = "Asia/Dhaka") -> str:
        """
        Get current time in specified timezone
        
        Args:
            timezone: Timezone string (e.g., 'Asia/Dhaka', 'America/New_York')
            
        Returns:
            Current time as string
        """
        try:
            from zoneinfo import ZoneInfo
            from datetime import datetime
            
            # Get current time in specified timezone
            tz = ZoneInfo(timezone)
            current_time = datetime.now(tz)
            
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            logger.info(f"Retrieved time for timezone {timezone}: {time_str}")
            return f"Current time in {timezone}: {time_str}"
            
        except Exception as e:
            logger.error(f"Error getting time: {str(e)}")
            return f"Error getting time for timezone {timezone}: {str(e)}"
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="current_time",
            func=self.get_current_time,
            description="Get current time in any timezone. Input should be a timezone string like 'Asia/Dhaka'."
        )

class WebSearchTool:
    """Tool for web searching (mock implementation)"""
    
    def search(self, query: str) -> str:
        """
        Perform web search
        
        Args:
            query: Search query
            
        Returns:
            Search results as string
        """
        
        logger.info(f"Web search for: {query}")
        
        return f"""
            Mock search results for "{query}":
            1. Result 1: Information about {query}
            2. Result 2: Latest updates on {query}
            3. Result 3: Expert opinions on {query}

            Note: This is a mock implementation. Integrate with a real search API for actual results.
            """
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="web_search",
            func=self.search,
            description="Search the web for information. Input should be a search query."
        )

class EmailTool:
    """Tool for email operations (mock implementation)"""
    
    def send_email(self, recipient: str, subject: str, body: str) -> str:
        """
        Send an email (mock implementation)
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body
            
        Returns:
            Status message
        """
        logger.info(f"Mock email sent to {recipient} with subject: {subject}")
        
        return f"""
            Email sent successfully (mock):
            - To: {recipient}
            - Subject: {subject}
            - Body preview: {body[:100]}...

            Note: This is a mock implementation. Configure SMTP settings for actual email sending.
            """
    
    def as_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="send_email",
            func=lambda x: self.send_email(**json.loads(x)),
            description="Send an email. Input should be JSON with 'recipient', 'subject', and 'body' fields."
        )

# Tool registry
AVAILABLE_TOOLS = {
    "weather": WeatherTool,
    "calculator": CalculatorTool,
    "timezone": TimezoneTool,
    "web_search": WebSearchTool,
    "email": EmailTool
}

def get_tool(tool_name: str) -> Optional[Tool]:
    """
    Get a tool by name
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool instance or None
    """
    if tool_name in AVAILABLE_TOOLS:
        tool_class = AVAILABLE_TOOLS[tool_name]
        return tool_class().as_tool()
    return None

def get_all_tools() -> List[Tool]:
    """Get all available tools"""
    tools = []
    for tool_name, tool_class in AVAILABLE_TOOLS.items():
        tools.append(tool_class().as_tool())
    return tools
