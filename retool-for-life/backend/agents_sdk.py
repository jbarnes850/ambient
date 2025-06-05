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
                trace_include_sensitive_data=True  # Enable for full trace visibility
            )
            
            # Use sync_to_async to handle the synchronous SDK in async context
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Generate unique trace ID
            trace_id = f"trace_{int(datetime.now().timestamp() * 1000000)}"
            
            # Run with tracing context
            current_trace = None
            with trace(f"Agent evaluation: {self.name}", trace_id=trace_id) as current_trace:
                result = await loop.run_in_executor(
                    None, 
                    lambda: Runner.run_sync(self.agent, user_message, config=config)
                )
            
            # Extract comprehensive trace data if available
            trace_data = None
            if capture_traces and current_trace:
                trace_data = self._extract_comprehensive_trace_data(current_trace, result)
            
            return {
                "message": result.final_output if hasattr(result, 'final_output') else str(result),
                "tool_calls": [],  # SDK handles tool calls internally
                "success": True,
                "trace_data": trace_data,
                "reasoning": result.final_output if hasattr(result, 'final_output') else str(result)[:500],
                "tools_used": self._extract_tools_used(result)
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "message": "I encountered an error processing your request. Please try again.",
                "tool_calls": [],
                "success": False,
                "error": str(e),
                "trace_data": None,
                "reasoning": f"Error occurred: {str(e)}",
                "tools_used": []
            }
    
    def _extract_comprehensive_trace_data(self, trace_obj: Any, result: Any) -> Dict[str, Any]:
        """Extract comprehensive trace data from OpenAI SDK trace object"""
        try:
            # Get trace information
            trace_data = {
                "trace_id": getattr(trace_obj, 'trace_id', f"trace_{int(datetime.now().timestamp())}"),
                "workflow_name": getattr(trace_obj, 'workflow_name', f"Agent evaluation: {self.name}"),
                "started_at": getattr(trace_obj, 'started_at', datetime.now().isoformat()),
                "ended_at": getattr(trace_obj, 'ended_at', datetime.now().isoformat()),
                "spans": [],
                "events": [],
                "metadata": getattr(trace_obj, 'metadata', {}),
                "total_duration_ms": 0,
                "llm_generations": [],
                "function_calls": [],
                "agent_steps": []
            }
            
            # Extract spans if available
            spans = getattr(trace_obj, 'spans', [])
            for span in spans:
                span_info = self._extract_span_data(span)
                trace_data["spans"].append(span_info)
                
                # Categorize spans by type
                span_type = span_info.get("span_type", "")
                if "generation" in span_type.lower():
                    trace_data["llm_generations"].append(span_info)
                elif "function" in span_type.lower():
                    trace_data["function_calls"].append(span_info)
                elif "agent" in span_type.lower():
                    trace_data["agent_steps"].append(span_info)
            
            # Calculate total duration
            if trace_data["started_at"] and trace_data["ended_at"]:
                try:
                    start = datetime.fromisoformat(trace_data["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(trace_data["ended_at"].replace("Z", "+00:00"))
                    trace_data["total_duration_ms"] = (end - start).total_seconds() * 1000
                except:
                    pass
            
            # Extract events
            events = getattr(trace_obj, 'events', [])
            for event in events:
                event_info = {
                    "timestamp": getattr(event, 'timestamp', datetime.now().isoformat()),
                    "event_type": type(event).__name__,
                    "data": getattr(event, 'data', {})
                }
                trace_data["events"].append(event_info)
            
            return trace_data
            
        except Exception as e:
            logger.error(f"Error extracting trace data: {str(e)}")
            return {
                "trace_id": f"trace_{int(datetime.now().timestamp())}",
                "error": f"Failed to extract trace data: {str(e)}",
                "spans": [],
                "events": []
            }
    
    def _extract_span_data(self, span: Any) -> Dict[str, Any]:
        """Extract detailed data from a single span"""
        try:
            span_info = {
                "span_id": getattr(span, 'span_id', None),
                "parent_id": getattr(span, 'parent_id', None),
                "span_type": type(span).__name__ if hasattr(span, "__class__") else "unknown",
                "started_at": getattr(span, 'started_at', None),
                "ended_at": getattr(span, 'ended_at', None),
                "duration_ms": None,
                "span_data": {}
            }
            
            # Calculate duration
            if span_info["started_at"] and span_info["ended_at"]:
                try:
                    start = datetime.fromisoformat(str(span_info["started_at"]).replace("Z", "+00:00"))
                    end = datetime.fromisoformat(str(span_info["ended_at"]).replace("Z", "+00:00"))
                    span_info["duration_ms"] = (end - start).total_seconds() * 1000
                except:
                    pass
            
            # Extract span-specific data
            if hasattr(span, 'span_data'):
                span_data = span.span_data
                if hasattr(span_data, '__dict__'):
                    span_info["span_data"] = {}
                    for key, value in span_data.__dict__.items():
                        if not key.startswith('_'):
                            # Convert non-serializable objects to strings
                            try:
                                json.dumps(value)  # Test if serializable
                                span_info["span_data"][key] = value
                            except:
                                span_info["span_data"][key] = str(value)
            
            return span_info
            
        except Exception as e:
            logger.error(f"Error extracting span data: {str(e)}")
            return {
                "span_type": "error",
                "error": str(e)
            }
    
    def _extract_tools_used(self, result: Any) -> List[str]:
        """Extract list of tools used during execution"""
        tools_used = []
        
        # Try to extract tool information from result
        if hasattr(result, 'tool_calls'):
            for tool_call in result.tool_calls:
                tool_name = getattr(tool_call, 'name', getattr(tool_call, 'tool_name', 'unknown'))
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
        
        # Also check our registered tools
        available_tools = list(self.tools.keys())
        for tool in available_tools:
            if tool in str(result):
                tools_used.append(tool)
        
        return tools_used
    
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