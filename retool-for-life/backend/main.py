"""Main FastAPI application for ReTool-for-Life"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
import os
import uuid

from config import settings
from orchestrator import MetaAgentOrchestrator, RLAIFOptimizer, load_test_scenarios
from agents_sdk import WellnessAgentSDK as WellnessAgent
from tools import approve_action, get_pending_approvals
from mock_apis import MockHealthAPI

# Initialize FastAPI app
app = FastAPI(
    title="ReTool-for-Life API",
    description="Meta-agent wellness platform with autonomous agents",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    def __init__(self):
        self.orchestrator = MetaAgentOrchestrator()
        self.optimizer = RLAIFOptimizer()
        self.users = self._load_users()
        self.websocket_manager = WebSocketManager()
        self.demo_results = {}
        self.agent_traces = {}
        self.evaluation_traces = {}
        
    def _load_users(self):
        """Load synthetic users from JSON"""
        try:
            with open("synthetic_users.json", "r") as f:
                return {u["id"]: u for u in json.load(f)}
        except Exception as e:
            print(f"Error loading users: {e}")
            # Return a default user for demo
            return {
                "demo-user-001": {
                    "id": "demo-user-001",
                    "name": "Demo User",
                    "phone": os.getenv("DEMO_PHONE_NUMBER", "+1234567890"),
                    "health_metrics": {
                        "avg_sleep_hours": 6.5,
                        "sleep_quality": 0.75,
                        "stress_level": "moderate"
                    },
                    "schedule": {
                        "work_hours": "09:00-18:00"
                    },
                    "preferences": {
                        "wellness_goals": ["better_sleep", "stress_reduction"],
                        "communication_style": "concise",
                        "automation_comfort": "high",
                        "purchase_approval": "required"
                    }
                }
            }

class WebSocketManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        for user_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_json(message)
            except:
                self.disconnect(user_id)


# Initialize app state after WebSocketManager is defined
app_state = AppState()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("ReTool-for-Life API starting up...")
    print(f"Loaded {len(app_state.users)} users")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ReTool-for-Life API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/users")
async def get_users():
    """Get all available demo users"""
    return {
        "users": [
            {
                "id": user["id"],
                "name": user["name"],
                "wellness_goals": user["preferences"]["wellness_goals"]
            }
            for user in app_state.users.values()
        ]
    }


@app.post("/api/users/{user_id}/generate-agent")
async def generate_agent(
    user_id: str,
    background_tasks: BackgroundTasks
):
    """Generate and deploy personalized wellness agent"""
    
    # Get user profile
    user = app_state.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Notify via WebSocket
    await app_state.websocket_manager.send_personal_message({
        "type": "agent_generation",
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }, user_id)
    
    try:
        # Generate agent suite
        agents = await app_state.orchestrator.generate_agent_suite(user)
        
        # Load test scenarios
        test_scenarios = load_test_scenarios()
        
        # Evaluate agents (now returns dict with scores and traces)
        evaluation_result = await app_state.orchestrator.evaluate_agents(agents, test_scenarios)
        scores = evaluation_result["scores"]
        traces = evaluation_result["traces"]
        
        # Deploy best agent
        best_agent_name = max(scores, key=scores.get)
        best_agent = next(a for a in agents if f"{a.name} ({a.model})" == best_agent_name)
        agent_id = app_state.orchestrator.deploy_agent(user_id, best_agent)
        
        # Initialize trace storage
        app_state.agent_traces[agent_id] = []
        
        # Store evaluation traces for later retrieval
        app_state.evaluation_traces = traces
        
        # Notify completion with trace data
        await app_state.websocket_manager.send_personal_message({
            "type": "agent_generation",
            "status": "completed",
            "agent_id": agent_id,
            "agent_name": best_agent.name,
            "evaluation_scores": scores,
            "evaluation_traces": traces,
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
        return {
            "agent_id": agent_id,
            "agent_name": best_agent.name,
            "agent_type": best_agent.__class__.__name__,
            "model": best_agent.model,
            "evaluation_scores": scores,
            "evaluation_traces": traces,
            "deployment_status": "active"
        }
        
    except Exception as e:
        await app_state.websocket_manager.send_personal_message({
            "type": "agent_generation",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, user_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}/agent-status")
async def get_agent_status(user_id: str):
    """Get current agent status and recent actions"""
    
    agent = app_state.orchestrator.get_active_agent(user_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="No active agent")
    
    # Get agent ID
    agent_id = None
    for aid in app_state.agent_traces.keys():
        if user_id in aid:
            agent_id = aid
            break
    
    # Get recent traces
    traces = app_state.agent_traces.get(agent_id, [])[-10:]
    
    # Calculate performance metrics
    rewards = await app_state.optimizer.calculate_daily_rewards(
        agent_id or f"{user_id}-unknown",
        traces
    )
    
    return {
        "agent": {
            "name": agent.name,
            "type": agent.__class__.__name__,
            "model": agent.model,
            "version": 1
        },
        "recent_actions": traces,
        "performance": rewards,
        "health_status": "active"
    }


@app.get("/api/evaluation-traces")
async def get_evaluation_traces():
    """Get the latest evaluation traces showing how agents were evaluated"""
    
    if not app_state.evaluation_traces:
        raise HTTPException(status_code=404, detail="No evaluation traces available")
    
    return {
        "traces": app_state.evaluation_traces,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/traces/{trace_id}/full")
async def get_full_trace_data(trace_id: str):
    """Get complete trace data including all spans and execution details"""
    
    # Search through all stored traces to find the requested trace_id
    full_trace_data = None
    
    # Check agent traces
    for agent_id, traces in app_state.agent_traces.items():
        for trace in traces:
            if trace.get("trace_data", {}).get("trace_id") == trace_id:
                full_trace_data = trace
                break
        if full_trace_data:
            break
    
    # Check evaluation traces
    if not full_trace_data:
        for agent_name, agent_traces in app_state.evaluation_traces.items():
            for trace in agent_traces:
                if trace.get("trace_data", {}).get("trace_id") == trace_id:
                    full_trace_data = trace
                    break
            if full_trace_data:
                break
    
    if not full_trace_data:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return {
        "trace_id": trace_id,
        "full_trace": full_trace_data,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/traces/{trace_id}/spans")
async def get_trace_spans(trace_id: str):
    """Get detailed span information for a trace including OpenAI SDK spans"""
    
    # Get the full trace data first
    full_trace_response = await get_full_trace_data(trace_id)
    trace_data = full_trace_response["full_trace"].get("trace_data", {})
    
    # Extract spans from OpenAI SDK trace data
    spans = trace_data.get("spans", [])
    events = trace_data.get("events", [])
    
    # Structure the span data for frontend consumption
    structured_spans = []
    for span in spans:
        span_info = {
            "span_id": getattr(span, "span_id", None),
            "parent_id": getattr(span, "parent_id", None),
            "span_type": type(span).__name__ if hasattr(span, "__class__") else "unknown",
            "started_at": getattr(span, "started_at", None),
            "ended_at": getattr(span, "ended_at", None),
            "duration_ms": None,
            "span_data": {}
        }
        
        # Calculate duration if timestamps available
        if span_info["started_at"] and span_info["ended_at"]:
            try:
                start = datetime.fromisoformat(span_info["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(span_info["ended_at"].replace("Z", "+00:00"))
                span_info["duration_ms"] = (end - start).total_seconds() * 1000
            except:
                pass
        
        # Extract span-specific data based on type
        if hasattr(span, "span_data"):
            span_data = span.span_data
            if hasattr(span_data, "__dict__"):
                span_info["span_data"] = {k: v for k, v in span_data.__dict__.items() if not k.startswith("_")}
        
        structured_spans.append(span_info)
    
    return {
        "trace_id": trace_id,
        "spans": structured_spans,
        "events": events,
        "total_spans": len(structured_spans),
        "execution_hierarchy": _build_span_hierarchy(structured_spans),
        "timestamp": datetime.now().isoformat()
    }


def _build_span_hierarchy(spans: List[Dict]) -> List[Dict]:
    """Build a hierarchical view of spans for better visualization"""
    
    # Create a map of span_id to span
    span_map = {span["span_id"]: span for span in spans if span["span_id"]}
    
    # Find root spans (no parent)
    root_spans = [span for span in spans if not span["parent_id"]]
    
    def build_children(parent_span):
        children = [span for span in spans if span["parent_id"] == parent_span["span_id"]]
        for child in children:
            child["children"] = build_children(child)
        return children
    
    # Build hierarchy
    for root in root_spans:
        root["children"] = build_children(root)
    
    return root_spans


@app.post("/api/users/{user_id}/chat")
async def chat_with_agent(user_id: str, message: dict):
    """Chat with the user's wellness agent"""
    
    agent = app_state.orchestrator.get_active_agent(user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="No active agent")
    
    user_message = message.get("message", "")
    
    # Process message with agent
    response = await agent.process_message(user_message)
    
    # Create trace
    trace = {
        "timestamp": datetime.now().isoformat(),
        "action": "chat",
        "input": user_message,
        "output": response.message,
        "tool_calls": [tc.dict() for tc in response.tool_calls],
        "status": "completed"
    }
    
    # Store trace
    agent_id = f"{user_id}-{agent.__class__.__name__}"
    if agent_id in app_state.agent_traces:
        app_state.agent_traces[agent_id].append(trace)
    
    # Send via WebSocket
    await app_state.websocket_manager.send_personal_message({
        "type": "agent_response",
        "response": response.dict(),
        "trace": trace,
        "timestamp": datetime.now().isoformat()
    }, user_id)
    
    return response.dict()


@app.post("/api/users/{user_id}/trigger-demo")
async def trigger_demo_sequence(user_id: str):
    """Run complete demo sequence"""
    
    agent = app_state.orchestrator.get_active_agent(user_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Generate agent first")
    
    results = []
    
    # Demo tasks based on PRD requirements
    demo_tasks = [
        {
            "time": "09:00",
            "description": "Morning wellness check",
            "prompt": "Pull my sleep data from last night and send me an SMS recap. Also check my calendar and ask if I want to move tomorrow's 07:30 1-on-1 meeting to optimize for better sleep."
        },
        {
            "time": "19:30",
            "description": "Evening reminder",
            "prompt": "Send me an SMS heads-up that screen-time lock starts at 22:00"
        },
        {
            "time": "22:00",
            "description": "Bedtime routine",
            "prompt": "Send me an SMS saying 'Locking distracting apps now' and then execute the iOS shortcut to lock apps and dim the screen."
        },
        {
            "time": "22:05",
            "description": "Sleep aid recommendation",
            "prompt": "Search the web for the best OTC melatonin products. Pick the top-rated one and send me an SMS with the recommendation and price."
        },
        {
            "time": "22:06",
            "description": "Purchase approval",
            "prompt": "If I approved the melatonin recommendation, execute the Amazon sandbox checkout to purchase it."
        }
    ]
    
    for task in demo_tasks:
        # Notify start
        await app_state.websocket_manager.send_personal_message({
            "type": "demo_task",
            "status": "started",
            "task": task,
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
        # Execute task
        try:
            response = await agent.process_message(task["prompt"])
            
            result = {
                "time": task["time"],
                "description": task["description"],
                "prompt": task["prompt"],
                "response": response.dict(),
                "status": "completed"
            }
            
            # Store trace
            trace = {
                "timestamp": datetime.now().isoformat(),
                "action": task["description"],
                "input": task["prompt"],
                "output": response.message,
                "tool_calls": [tc.dict() for tc in response.tool_calls],
                "status": "completed"
            }
            
            agent_id = f"{user_id}-{agent.__class__.__name__}"
            if agent_id in app_state.agent_traces:
                app_state.agent_traces[agent_id].append(trace)
            
            results.append(result)
            
            # Notify completion
            await app_state.websocket_manager.send_personal_message({
                "type": "demo_task",
                "status": "completed",
                "task": task,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }, user_id)
            
            # Brief pause for demo effect
            await asyncio.sleep(2)
            
        except Exception as e:
            result = {
                "time": task["time"],
                "description": task["description"],
                "error": str(e),
                "status": "failed"
            }
            results.append(result)
    
    # Trigger RLAIF improvement
    agent_id = f"{user_id}-{agent.__class__.__name__}"
    traces = app_state.agent_traces.get(agent_id, [])
    rewards = await app_state.optimizer.calculate_daily_rewards(agent_id, traces)
    
    # Update agent if needed
    agent_upgraded = False
    if sum(rewards.values()) / len(rewards) < 0.8:
        try:
            new_agent = await app_state.optimizer.update_agent(agent, rewards)
            app_state.orchestrator.active_agents[user_id] = new_agent
            agent_upgraded = True
            
            # Notify upgrade
            await app_state.websocket_manager.send_personal_message({
                "type": "agent_upgrade",
                "old_version": 1,
                "new_version": 2,
                "improvements": [k for k, v in rewards.items() if v < 0.7],
                "timestamp": datetime.now().isoformat()
            }, user_id)
        except Exception as e:
            print(f"Error upgrading agent: {e}")
    
    # Store demo results
    app_state.demo_results[user_id] = {
        "results": results,
        "performance_metrics": rewards,
        "agent_upgraded": agent_upgraded,
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "demo_results": results,
        "performance_metrics": rewards,
        "agent_upgraded": agent_upgraded,
        "total_actions": len(results)
    }


@app.get("/api/approvals/pending")
async def get_approvals():
    """Get all pending approvals"""
    return await get_pending_approvals()


@app.post("/api/approvals/{approval_id}/approve")
async def approve_pending_action(approval_id: str):
    """Approve a pending action"""
    result = await approve_action(approval_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    # Broadcast approval
    await app_state.websocket_manager.broadcast({
        "type": "approval_processed",
        "approval_id": approval_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    
    return result


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await app_state.websocket_manager.connect(user_id, websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        app_state.websocket_manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        app_state.websocket_manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)