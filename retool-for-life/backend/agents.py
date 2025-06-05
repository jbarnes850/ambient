"""OpenAI Agents SDK implementation for wellness agents"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ToolCall(BaseModel):
    """Model for tool calls"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None


class AgentResponse(BaseModel):
    """Model for agent responses"""
    message: str
    tool_calls: List[ToolCall] = []
    reasoning: Optional[str] = None


class WellnessAgent:
    """Base wellness agent with common tools and behaviors"""
    
    def __init__(self, user_profile: Dict[str, Any], model: str = "gpt-4o"):
        self.user_profile = user_profile
        self.model = model
        self.name = f"Wellness Agent for {user_profile['name']}"
        self.tools = self._get_tools()
        self.instructions = self._generate_instructions()
        self.conversation_history = []
        
    def _generate_instructions(self) -> str:
        """Generate personalized instructions based on user profile"""
        return f"""
        You are a personalized wellness agent for {self.user_profile['name']} with the following profile:
        - Sleep average: {self.user_profile['health_metrics']['avg_sleep_hours']} hours
        - Work schedule: {self.user_profile['schedule']['work_hours']}
        - Health goals: {', '.join(self.user_profile['preferences']['wellness_goals'])}
        - Stress level: {self.user_profile['health_metrics']['stress_level']}
        
        Your responsibilities:
        1. Monitor health metrics and provide insights
        2. Optimize calendar for better work-life balance
        3. Send timely reminders for wellness activities
        4. Recommend wellness products when beneficial
        
        Always be respectful of user preferences. For purchases, approval is {self.user_profile['preferences']['purchase_approval']}.
        Communication style should be {self.user_profile['preferences']['communication_style']}.
        
        When using tools, always explain what you're doing and why.
        """
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Define available tools for the agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "send_sms",
                    "description": "Send an SMS message to the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send"
                            },
                            "require_approval": {
                                "type": "boolean",
                                "description": "Whether to require approval before sending",
                                "default": True
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_health_metrics",
                    "description": "Get current health metrics including sleep, activity, stress, and hydration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric_type": {
                                "type": "string",
                                "enum": ["sleep", "activity", "stress", "hydration", "all"],
                                "description": "Type of health metric to retrieve"
                            }
                        },
                        "required": ["metric_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_wellness_products",
                    "description": "Search for wellness products",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Product search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_calendar",
                    "description": "Analyze calendar and suggest optimizations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "optimization_type": {
                                "type": "string",
                                "enum": ["sleep", "breaks", "focus_time"],
                                "description": "Type of optimization to perform"
                            }
                        },
                        "required": ["optimization_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "commerce_buy",
                    "description": "Execute a purchase through the commerce API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "Product ID"
                            },
                            "product_name": {
                                "type": "string",
                                "description": "Product name"
                            },
                            "price": {
                                "type": "number",
                                "description": "Product price"
                            },
                            "require_approval": {
                                "type": "boolean",
                                "description": "Whether to require approval before purchase",
                                "default": True
                            }
                        },
                        "required": ["product_id", "product_name", "price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_ios_shortcut",
                    "description": "Execute an iOS Shortcut to control device features",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shortcut_name": {
                                "type": "string",
                                "description": "Name of the shortcut to execute",
                                "enum": ["lock_apps", "sleep_mode", "morning_routine"]
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Optional parameters for the shortcut"
                            }
                        },
                        "required": ["shortcut_name"]
                    }
                }
            }
        ]
    
    async def process_message(self, user_message: str) -> AgentResponse:
        """Process a user message and return agent response"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": self.instructions},
            *self.conversation_history
        ]
        
        # Call OpenAI API with tools
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message
        tool_calls = []
        
        # Process tool calls if any
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tc = ToolCall(
                    tool_name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                )
                # Execute tool and get result
                tc.result = await self._execute_tool(tc.tool_name, tc.arguments)
                tool_calls.append(tc)
        
        # Add assistant message to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [tc.dict() for tc in tool_calls] if tool_calls else None
        })
        
        return AgentResponse(
            message=assistant_message.content or "I'm processing your request...",
            tool_calls=tool_calls,
            reasoning=None  # Could extract from response if needed
        )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call and return result"""
        # Import tools module to avoid circular imports
        from tools import (
            send_sms, get_health_metrics, 
            search_wellness_products, optimize_calendar,
            web_search, commerce_buy, execute_ios_shortcut
        )
        
        tool_map = {
            "send_sms": send_sms,
            "get_health_metrics": get_health_metrics,
            "search_wellness_products": search_wellness_products,
            "optimize_calendar": optimize_calendar,
            "web_search": web_search,
            "commerce_buy": commerce_buy,
            "execute_ios_shortcut": execute_ios_shortcut
        }
        
        if tool_name in tool_map:
            # Add user_id to arguments if needed
            if tool_name in ["get_health_metrics", "optimize_calendar"]:
                arguments["user_id"] = self.user_profile["id"]
            elif tool_name == "send_sms":
                arguments["to_number"] = self.user_profile.get("phone", os.getenv("DEMO_PHONE_NUMBER"))
            elif tool_name == "commerce_buy":
                arguments["user_id"] = self.user_profile["id"]
            
            return await tool_map[tool_name](**arguments)
        
        return {"error": f"Unknown tool: {tool_name}"}


class SleepOptimizationAgent(WellnessAgent):
    """Specialized agent for sleep optimization"""
    
    def _generate_instructions(self) -> str:
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        As a Sleep Optimization Specialist, focus on:
        - Analyzing sleep patterns and quality
        - Providing personalized sleep recommendations
        - Monitoring bedtime routines
        - Suggesting products that improve sleep quality
        - Creating optimal wind-down schedules
        """


class StressManagementAgent(WellnessAgent):
    """Specialized agent for stress management"""
    
    def _generate_instructions(self) -> str:
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        As a Stress Management Specialist, focus on:
        - Monitoring stress indicators
        - Suggesting breathing exercises and breaks
        - Recommending stress-relief products
        - Optimizing schedules to reduce stress
        - Providing mindfulness reminders
        """


class FitnessAgent(WellnessAgent):
    """Specialized agent for fitness and activity"""
    
    def _generate_instructions(self) -> str:
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        As a Fitness Coach, focus on:
        - Tracking daily activity levels
        - Suggesting exercise routines
        - Monitoring sedentary time
        - Recommending fitness products
        - Creating movement reminders
        """


class NutritionAgent(WellnessAgent):
    """Specialized agent for nutrition and hydration"""
    
    def _generate_instructions(self) -> str:
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        As a Nutrition Advisor, focus on:
        - Monitoring hydration levels
        - Suggesting healthy eating habits
        - Recommending nutritional supplements
        - Creating meal timing reminders
        - Tracking water intake goals
        """