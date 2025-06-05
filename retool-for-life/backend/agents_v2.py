"""OpenAI Agents SDK implementation for wellness agents"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
from agents import Agent, Run, Thread
from agents.tools import Tool
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class HealthMetricsTool(Tool):
    """Tool for getting health metrics"""
    name = "get_health_metrics"
    description = "Get current health metrics including sleep, activity, stress, and hydration"
    
    async def call(self, user_id: str, metric_type: str = "all") -> Dict[str, Any]:
        from tools import get_health_metrics
        return await get_health_metrics(user_id, metric_type)


class SendSMSTool(Tool):
    """Tool for sending SMS messages"""
    name = "send_sms"
    description = "Send an SMS message to the user"
    
    async def call(self, message: str, to_number: str, require_approval: bool = True) -> Dict[str, Any]:
        from tools import send_sms
        return await send_sms(message, to_number, require_approval)


class SearchWellnessProductsTool(Tool):
    """Tool for searching wellness products"""
    name = "search_wellness_products"
    description = "Search for wellness products"
    
    async def call(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        from tools import search_wellness_products
        return await search_wellness_products(query, max_results)


class OptimizeCalendarTool(Tool):
    """Tool for calendar optimization"""
    name = "optimize_calendar"
    description = "Analyze calendar and suggest optimizations"
    
    async def call(self, user_id: str, optimization_type: str = "sleep") -> Dict[str, Any]:
        from tools import optimize_calendar
        return await optimize_calendar(user_id, optimization_type)


class WellnessAgentV2:
    """Base wellness agent using OpenAI Agents SDK"""
    
    def __init__(self, user_profile: Dict[str, Any], model: str = "gpt-4o"):
        self.user_profile = user_profile
        self.model = model
        self.name = f"Wellness Agent for {user_profile['name']}"
        
        # Create agent with OpenAI Agents SDK
        self.agent = Agent(
            name=self.name,
            instructions=self._generate_instructions(),
            model=self.model,
            tools=[
                HealthMetricsTool(),
                SendSMSTool(),
                SearchWellnessProductsTool(),
                OptimizeCalendarTool()
            ]
        )
        
        # Create a thread for conversation
        self.thread = Thread()
        
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
        
        Important context:
        - When calling get_health_metrics, always pass user_id as "{self.user_profile['id']}"
        - When calling send_sms, use to_number as "{self.user_profile.get('phone', os.getenv('DEMO_PHONE_NUMBER'))}"
        - When calling optimize_calendar, always pass user_id as "{self.user_profile['id']}"
        """
    
    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process a user message and return agent response"""
        # Create a message in the thread
        self.thread.add_message(role="user", content=user_message)
        
        # Run the agent
        run = Run(agent=self.agent, thread=self.thread)
        result = await run.run()
        
        # Get the last assistant message
        messages = self.thread.get_messages()
        assistant_message = None
        tool_calls = []
        
        for msg in reversed(messages):
            if msg.role == "assistant":
                assistant_message = msg.content
                # Extract tool calls from the run
                if hasattr(run, 'tool_calls'):
                    tool_calls = run.tool_calls
                break
        
        return {
            "message": assistant_message or "I'm processing your request...",
            "tool_calls": tool_calls,
            "thread_id": self.thread.id if hasattr(self.thread, 'id') else None
        }


class SleepOptimizationAgentV2(WellnessAgentV2):
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


class StressManagementAgentV2(WellnessAgentV2):
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


class FitnessAgentV2(WellnessAgentV2):
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


class NutritionAgentV2(WellnessAgentV2):
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