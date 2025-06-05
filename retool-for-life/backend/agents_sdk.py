"""OpenAI Agents SDK implementation for wellness agents"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import asyncio
from agents import Agent, Runner, RunConfig, trace
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WellnessAgentSDK:
    """Base wellness agent using OpenAI Agents SDK"""
    
    def __init__(self, user_profile: Dict[str, Any], model: str = "gpt-4.1"):
        self.user_profile = user_profile
        self.model = model
        self.name = f"Wellness Agent for {user_profile['name']}"
        self.tools = {}
        self._setup_tools()
        
        # Create agent with OpenAI Agents SDK
        self.agent = Agent(
            name=self.name,
            instructions=self._generate_instructions(),
            model=self.model
        )
        
    def _setup_tools(self):
        """Setup tools available to the agent"""
        # Import tools from our tools module
        from tools import (
            get_health_metrics, 
            send_sms, 
            search_wellness_products, 
            optimize_calendar
        )
        
        # Register tools as functions the agent can use
        self.tools = {
            "get_health_metrics": get_health_metrics,
            "send_sms": send_sms,
            "search_wellness_products": search_wellness_products,
            "optimize_calendar": optimize_calendar
        }
        
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
        
        When you need to take actions, describe what you want to do and I'll help execute the appropriate tools.
        
        Important context:
        - User ID: {self.user_profile['id']}
        - Phone number: {self.user_profile.get('phone', os.getenv('DEMO_PHONE_NUMBER'))}
        """
    
    async def process_message(self, user_message: str, capture_traces: bool = False) -> Dict[str, Any]:
        """Process a user message and return agent response with optional tracing"""
        try:
            # Configure tracing
            config = RunConfig(
                tracing_disabled=not capture_traces,
                trace_include_sensitive_data=False  # Privacy-conscious by default
            )
            
            # Use sync_to_async to handle the synchronous SDK in async context
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Run with tracing context
            with trace(f"Agent evaluation: {self.name}"):
                result = await loop.run_in_executor(
                    None, 
                    lambda: Runner.run_sync(self.agent, user_message, config=config)
                )
            
            # Extract trace data if available
            trace_data = None
            if capture_traces and hasattr(result, 'trace'):
                trace_data = {
                    "trace_id": getattr(result.trace, 'id', None),
                    "spans": getattr(result.trace, 'spans', []),
                    "events": getattr(result.trace, 'events', [])
                }
            
            return {
                "message": result.final_output if hasattr(result, 'final_output') else str(result),
                "tool_calls": [],  # SDK handles tool calls internally
                "success": True,
                "trace_data": trace_data
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "message": "I encountered an error processing your request. Please try again.",
                "tool_calls": [],
                "success": False,
                "error": str(e),
                "trace_data": None
            }
    
    async def execute_demo_task(self, task_description: str) -> Dict[str, Any]:
        """Execute a specific demo task"""
        return await self.process_message(task_description)


class SleepOptimizationAgentSDK(WellnessAgentSDK):
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
        
        For the demo workflow:
        - At 09:00: Analyze last night's sleep and suggest schedule adjustments
        - At 19:30: Send reminder about screen-time lock at 22:00
        - At 22:00: Activate screen-time restrictions
        - At 22:05: Search for and recommend sleep aids like melatonin
        """


class StressManagementAgentSDK(WellnessAgentSDK):
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


class FitnessAgentSDK(WellnessAgentSDK):
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


class NutritionAgentSDK(WellnessAgentSDK):
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


# Agent factory for creating specialized agents
def create_wellness_agent_sdk(
    agent_type: str, 
    user_profile: Dict[str, Any], 
    model: str = "gpt-4.1"
) -> WellnessAgentSDK:
    """Factory function to create specialized wellness agents"""
    
    agent_classes = {
        "sleep": SleepOptimizationAgentSDK,
        "stress": StressManagementAgentSDK,
        "fitness": FitnessAgentSDK,
        "nutrition": NutritionAgentSDK,
        "general": WellnessAgentSDK
    }
    
    agent_class = agent_classes.get(agent_type, WellnessAgentSDK)
    return agent_class(user_profile, model)