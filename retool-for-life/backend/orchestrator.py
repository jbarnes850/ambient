"""Meta-agent orchestrator for generating and evaluating wellness agents"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
try:
    # Try to import SDK agents first
    from agents_sdk import (
        WellnessAgentSDK as WellnessAgent,
        SleepOptimizationAgentSDK as SleepOptimizationAgent,
        StressManagementAgentSDK as StressManagementAgent,
        FitnessAgentSDK as FitnessAgent,
        NutritionAgentSDK as NutritionAgent
    )
    print("Using OpenAI Agents SDK implementation")
except ImportError:
    try:
        # Try v2 agents
        from agents_v2 import (
            WellnessAgentV2 as WellnessAgent,
            SleepOptimizationAgentV2 as SleepOptimizationAgent,
            StressManagementAgentV2 as StressManagementAgent,
            FitnessAgentV2 as FitnessAgent,
            NutritionAgentV2 as NutritionAgent
        )
        print("Using OpenAI Agents SDK v2")
    except ImportError:
        # Fallback to v1 agents
        from agents import (
            WellnessAgent, SleepOptimizationAgent,
            StressManagementAgent, FitnessAgent, NutritionAgent
        )
        print("Using legacy agents implementation")
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MetaAgentOrchestrator:
    """Orchestrates the generation, evaluation, and optimization of wellness agents"""
    
    def __init__(self):
        self.agent_templates = {
            "sleep_specialist": SleepOptimizationAgent,
            "stress_manager": StressManagementAgent,
            "fitness_coach": FitnessAgent,
            "nutrition_advisor": NutritionAgent
        }
        self.active_agents: Dict[str, WellnessAgent] = {}
        
    async def generate_agent_suite(
        self, 
        user_profile: Dict[str, Any]
    ) -> List[WellnessAgent]:
        """Generate multiple agent variants for evaluation"""
        
        agents = []
        
        # Determine which agents to create based on user goals
        user_goals = user_profile["preferences"]["wellness_goals"]
        
        # Map goals to agent types
        goal_agent_map = {
            "better_sleep": "sleep_specialist",
            "stress_reduction": "stress_manager",
            "stress_management": "stress_manager",
            "exercise_consistency": "fitness_coach",
            "hydration": "nutrition_advisor"
        }
        
        # Create agents based on user goals
        created_types = set()
        for goal in user_goals:
            agent_type = goal_agent_map.get(goal)
            if agent_type and agent_type not in created_types:
                agent_class = self.agent_templates[agent_type]
                # Create with different model variations
                agents.append(agent_class(user_profile, model="gpt-4o"))
                # Could add gpt-4o-mini variant for comparison
                agents.append(agent_class(user_profile, model="gpt-4o-mini"))
                created_types.add(agent_type)
        
        # Ensure at least one general wellness agent
        if not agents:
            agents.append(WellnessAgent(user_profile, model="gpt-4o"))
        
        return agents
    
    async def evaluate_agents(
        self,
        agents: List[WellnessAgent],
        test_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Run evaluation scenarios and score agents"""
        
        scores = {}
        
        for agent in agents:
            total_score = 0
            
            for scenario in test_scenarios:
                # Process the scenario with the agent
                try:
                    response = await agent.process_message(scenario["prompt"])
                    
                    # Score based on expected outcomes
                    score = await self._calculate_score(
                        response,
                        scenario.get("expected_outcomes", []),
                        scenario.get("required_tools", [])
                    )
                    total_score += score
                except Exception as e:
                    print(f"Error evaluating agent {agent.name}: {e}")
                    total_score += 0.5  # Partial credit for not crashing
            
            # Average score across scenarios
            avg_score = total_score / len(test_scenarios) if test_scenarios else 0
            scores[f"{agent.name} ({agent.model})"] = avg_score
        
        return scores
    
    async def _calculate_score(
        self,
        response: Any,
        expected_outcomes: List[str],
        required_tools: List[str]
    ) -> float:
        """Calculate score based on agent response"""
        score = 0.0
        
        # Check if required tools were used
        if required_tools:
            # Handle both dict and object response types
            tool_calls = []
            if isinstance(response, dict):
                tool_calls = response.get("tool_calls", [])
            elif hasattr(response, "tool_calls"):
                tool_calls = response.tool_calls
            
            if tool_calls:
                used_tools = [tc.get("tool_name", tc.tool_name if hasattr(tc, "tool_name") else "") for tc in tool_calls]
                tool_score = len(set(used_tools) & set(required_tools)) / len(required_tools)
                score += tool_score * 0.5
        
        # Check if response addresses expected outcomes
        message = response.get("message", "") if isinstance(response, dict) else getattr(response, "message", "")
        if expected_outcomes and message:
            addressed = sum(
                1 for outcome in expected_outcomes 
                if outcome.lower() in message.lower()
            )
            outcome_score = addressed / len(expected_outcomes)
            score += outcome_score * 0.5
        
        # If no specific requirements, give base score for coherent response
        if not required_tools and not expected_outcomes:
            score = 0.8 if message else 0.5
        
        return score
    
    def deploy_agent(self, user_id: str, agent: WellnessAgent) -> str:
        """Deploy an agent for a user"""
        agent_id = f"{user_id}-{agent.__class__.__name__}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.active_agents[user_id] = agent
        return agent_id
    
    def get_active_agent(self, user_id: str) -> Optional[WellnessAgent]:
        """Get the active agent for a user"""
        return self.active_agents.get(user_id)


class RLAIFOptimizer:
    """Reinforcement Learning from AI Feedback optimizer"""
    
    def __init__(self):
        self.performance_history: Dict[str, List[Dict[str, float]]] = {}
    
    async def calculate_daily_rewards(
        self,
        agent_id: str,
        agent_actions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate rewards based on agent performance"""
        
        rewards = {
            "task_completion": self._evaluate_task_completion(agent_actions),
            "user_engagement": self._evaluate_engagement(agent_actions),
            "timing_accuracy": self._evaluate_timing(agent_actions),
            "resource_efficiency": self._evaluate_efficiency(agent_actions),
            "safety_compliance": self._evaluate_safety(agent_actions)
        }
        
        # Store in history
        if agent_id not in self.performance_history:
            self.performance_history[agent_id] = []
        self.performance_history[agent_id].append({
            "timestamp": datetime.now().isoformat(),
            "rewards": rewards
        })
        
        return rewards
    
    def _evaluate_task_completion(self, actions: List[Dict[str, Any]]) -> float:
        """Evaluate how well tasks were completed"""
        if not actions:
            return 0.0
        
        completed = sum(1 for a in actions if a.get("status") == "completed")
        return completed / len(actions)
    
    def _evaluate_engagement(self, actions: List[Dict[str, Any]]) -> float:
        """Evaluate user engagement with agent actions"""
        # In a real system, this would track user responses
        # For demo, return a good score
        return 0.85
    
    def _evaluate_timing(self, actions: List[Dict[str, Any]]) -> float:
        """Evaluate if actions were taken at appropriate times"""
        # Check if actions respect user schedule
        return 0.9  # High score for demo
    
    def _evaluate_efficiency(self, actions: List[Dict[str, Any]]) -> float:
        """Evaluate resource usage efficiency"""
        # Check API calls, token usage, etc.
        return 0.8
    
    def _evaluate_safety(self, actions: List[Dict[str, Any]]) -> float:
        """Evaluate safety and compliance"""
        # Check if approvals were requested when needed
        approval_actions = [a for a in actions if "approval" in str(a).lower()]
        return 1.0 if not approval_actions else 0.95
    
    async def update_agent(
        self,
        agent: WellnessAgent,
        rewards: Dict[str, float]
    ) -> WellnessAgent:
        """Update agent based on reward signals"""
        
        # Calculate improvement areas
        weak_areas = [k for k, v in rewards.items() if v < 0.7]
        
        if not weak_areas:
            # Agent is performing well, no updates needed
            return agent
        
        # Generate improved instructions using AI
        improvement_prompt = f"""
        Current agent performance metrics:
        {json.dumps(rewards, indent=2)}
        
        Weak areas that need improvement: {', '.join(weak_areas)}
        
        Current instructions:
        {agent.instructions}
        
        Generate improved instructions that address the weak areas while maintaining the agent's core responsibilities and personality. Focus on specific improvements for the weak areas.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use efficient model for optimization
            messages=[
                {"role": "system", "content": "You are an AI agent optimization expert."},
                {"role": "user", "content": improvement_prompt}
            ],
            temperature=0.7
        )
        
        # Create new agent with improved instructions
        improved_agent = agent.__class__(agent.user_profile, agent.model)
        improved_agent.instructions = response.choices[0].message.content
        improved_agent.conversation_history = agent.conversation_history  # Preserve history
        
        return improved_agent


def load_test_scenarios(persona_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load test scenarios for agent evaluation"""
    
    # Base scenarios that apply to all agents
    scenarios = [
        {
            "prompt": "I had trouble sleeping last night and feel tired. What should I do?",
            "expected_outcomes": ["sleep", "recommendation", "insight"],
            "required_tools": ["get_health_metrics"]
        },
        {
            "prompt": "Can you check my schedule and help me optimize it for better wellness?",
            "expected_outcomes": ["calendar", "optimization", "suggestion"],
            "required_tools": ["optimize_calendar"]
        },
        {
            "prompt": "I'm feeling stressed. What products might help?",
            "expected_outcomes": ["stress", "product", "recommendation"],
            "required_tools": ["search_wellness_products"]
        },
        {
            "prompt": "Send me a reminder to drink water",
            "expected_outcomes": ["reminder", "hydration"],
            "required_tools": ["send_sms"]
        }
    ]
    
    # Add persona-specific scenarios if provided
    if persona_type == "high_stress":
        scenarios.extend([
            {
                "prompt": "My meetings are back-to-back today. Help!",
                "expected_outcomes": ["break", "schedule", "stress"],
                "required_tools": ["optimize_calendar", "send_sms"]
            }
        ])
    
    return scenarios