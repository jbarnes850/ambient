"""Tool implementations for wellness agents"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import uuid
from twilio.rest import Client
from dotenv import load_dotenv
from mock_apis import MockHealthAPI, MockCalendarAPI, MockCommerceAPI

# Load environment variables
load_dotenv()

# Initialize Twilio client (real integration)
twilio_client = None
if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
    try:
        twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
    except Exception as e:
        print(f"Warning: Could not initialize Twilio client: {e}")

# Approval queue for demo purposes
approval_queue: Dict[str, Dict[str, Any]] = {}


def generate_approval_id() -> str:
    """Generate unique approval ID"""
    return f"approval-{uuid.uuid4().hex[:8]}"


async def send_sms(
    message: str,
    to_number: str,
    require_approval: bool = True
) -> Dict[str, Any]:
    """Send SMS message via Twilio"""
    
    if require_approval:
        # Store in approval queue for demo
        approval_id = generate_approval_id()
        approval_queue[approval_id] = {
            "type": "sms",
            "message": message,
            "to_number": to_number,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        return {
            "status": "pending_approval",
            "message": message,
            "approval_id": approval_id,
            "approval_required": True
        }
    
    # Send actual SMS if Twilio is configured
    if twilio_client:
        try:
            message_obj = twilio_client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=to_number
            )
            return {
                "status": "sent",
                "message_sid": message_obj.sid,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "to_number": to_number
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": message
            }
    else:
        # Mock response if Twilio not configured
        return {
            "status": "sent_mock",
            "message_sid": f"mock-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "to_number": to_number,
            "note": "Twilio not configured - this is a mock response"
        }


async def get_health_metrics(
    user_id: str,
    metric_type: str = "all"
) -> Dict[str, Any]:
    """Get health metrics from mock API"""
    
    results = {}
    
    if metric_type in ["sleep", "all"]:
        results["sleep"] = await MockHealthAPI.get_sleep_metrics(user_id)
    
    if metric_type in ["activity", "all"]:
        results["activity"] = await MockHealthAPI.get_activity_data(user_id)
    
    if metric_type in ["stress", "all"]:
        results["stress"] = await MockHealthAPI.get_stress_metrics(user_id)
    
    if metric_type in ["hydration", "all"]:
        results["hydration"] = await MockHealthAPI.get_hydration_data(user_id)
    
    # If single metric requested, return just that
    if metric_type != "all" and metric_type in results:
        return results[metric_type]
    
    return results


async def search_wellness_products(
    query: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Search for wellness products using mock API"""
    
    products = await MockCommerceAPI.search_wellness_products(query, max_results)
    
    # Add recommendation scores based on query
    for product in products:
        # Simple relevance scoring
        if query.lower() in product["name"].lower():
            product["relevance_score"] = 0.9
        elif any(word in product["description"].lower() for word in query.lower().split()):
            product["relevance_score"] = 0.7
        else:
            product["relevance_score"] = 0.5
    
    # Sort by relevance and rating
    products.sort(key=lambda x: (x["relevance_score"], x["rating"]), reverse=True)
    
    return products


async def optimize_calendar(
    user_id: str,
    optimization_type: str = "sleep"
) -> Dict[str, Any]:
    """Analyze and optimize calendar for wellness"""
    
    # Get calendar events
    events = await MockCalendarAPI.get_calendar_events(user_id)
    
    # Analyze schedule density
    analysis = await MockCalendarAPI.analyze_schedule_density(events)
    
    # Generate specific optimizations based on type
    optimizations = []
    
    if optimization_type == "sleep":
        # Check for late meetings
        late_meetings = [e for e in events if e["start"].split("T")[1] >= "18:00"]
        if late_meetings:
            optimizations.append({
                "type": "reschedule",
                "description": f"Consider moving {len(late_meetings)} evening meetings earlier for better sleep",
                "impact": "high",
                "affected_events": [m["id"] for m in late_meetings]
            })
        
        optimizations.append({
            "type": "block_time",
            "description": "Block 21:00-22:00 for wind-down routine",
            "impact": "high",
            "suggested_time": "21:00-22:00"
        })
    
    elif optimization_type == "breaks":
        # Find back-to-back meetings
        for i in range(len(events) - 1):
            if events[i]["end"] == events[i + 1]["start"]:
                optimizations.append({
                    "type": "add_buffer",
                    "description": f"Add 15-minute break between '{events[i]['title']}' and '{events[i + 1]['title']}'",
                    "impact": "medium",
                    "between_events": [events[i]["id"], events[i + 1]["id"]]
                })
        
        optimizations.append({
            "type": "block_time",
            "description": "Schedule 5-minute breaks every hour",
            "impact": "medium",
            "frequency": "hourly"
        })
    
    elif optimization_type == "focus_time":
        # Find time slots for deep work
        optimizations.append({
            "type": "block_time",
            "description": "Reserve 9:00-11:00 for focused work (no meetings)",
            "impact": "high",
            "suggested_time": "09:00-11:00"
        })
        
        if analysis["meeting_hours"] > 5:
            optimizations.append({
                "type": "reduce_meetings",
                "description": "Consider making some meetings async or shorter",
                "impact": "high",
                "current_load": f"{analysis['meeting_hours']} hours of meetings"
            })
    
    return {
        "current_schedule": events,
        "analysis": analysis,
        "optimizations": optimizations,
        "optimization_type": optimization_type,
        "timestamp": datetime.now().isoformat()
    }


async def approve_action(approval_id: str) -> Dict[str, Any]:
    """Approve a pending action"""
    if approval_id not in approval_queue:
        return {"status": "error", "message": "Approval ID not found"}
    
    action = approval_queue[approval_id]
    action["status"] = "approved"
    action["approved_at"] = datetime.now().isoformat()
    
    # Execute the approved action
    if action["type"] == "sms":
        result = await send_sms(
            message=action["message"],
            to_number=action["to_number"],
            require_approval=False
        )
        action["execution_result"] = result
    
    return {
        "status": "approved",
        "approval_id": approval_id,
        "action": action
    }


async def get_pending_approvals() -> List[Dict[str, Any]]:
    """Get all pending approvals"""
    return [
        {"approval_id": aid, **action}
        for aid, action in approval_queue.items()
        if action["status"] == "pending"
    ]


async def commerce_buy(
    product_id: str,
    product_name: str,
    price: float,
    user_id: str,
    require_approval: bool = True
) -> Dict[str, Any]:
    """Execute purchase through commerce API (Stripe MCP Server simulation)"""
    
    if require_approval:
        # Store in approval queue for demo
        approval_id = generate_approval_id()
        approval_queue[approval_id] = {
            "type": "purchase",
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        return {
            "status": "pending_approval",
            "product": product_name,
            "price": price,
            "approval_id": approval_id,
            "approval_required": True,
            "message": f"Purchase approval required for {product_name} (${price})"
        }
    
    # Simulate Amazon sandbox checkout
    order_id = f"AMZ-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "status": "completed",
        "order_id": order_id,
        "product_id": product_id,
        "product_name": product_name,
        "price": price,
        "payment_method": "Stripe MCP Server (sandbox)",
        "delivery_date": "2-3 business days",
        "timestamp": datetime.now().isoformat(),
        "message": f"Successfully purchased {product_name} via Amazon sandbox"
    }


async def execute_ios_shortcut(
    shortcut_name: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute iOS Shortcut (computer.use simulation)"""
    
    # Map of available shortcuts for the demo
    available_shortcuts = {
        "lock_apps": {
            "description": "Lock distracting apps and dim screen",
            "actions": ["Lock Instagram", "Lock Twitter", "Lock TikTok", "Dim screen to 20%"]
        },
        "sleep_mode": {
            "description": "Enable full sleep mode",
            "actions": ["Enable Do Not Disturb", "Lock all apps", "Dim screen", "Enable Night Shift"]
        },
        "morning_routine": {
            "description": "Morning wellness routine",
            "actions": ["Disable Do Not Disturb", "Show weather", "Show calendar", "Play morning playlist"]
        }
    }
    
    if shortcut_name not in available_shortcuts:
        return {
            "status": "error",
            "message": f"Shortcut '{shortcut_name}' not found",
            "available_shortcuts": list(available_shortcuts.keys())
        }
    
    shortcut_info = available_shortcuts[shortcut_name]
    
    # Simulate execution
    return {
        "status": "executed",
        "shortcut_name": shortcut_name,
        "description": shortcut_info["description"],
        "actions_performed": shortcut_info["actions"],
        "timestamp": datetime.now().isoformat(),
        "parameters": parameters or {},
        "message": f"Successfully executed iOS Shortcut: {shortcut_name}"
    }


async def web_search(
    query: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """Search the web for information (web.search tool)"""
    
    # Simulate web search results for wellness products
    if "melatonin" in query.lower():
        results = [
            {
                "title": "Nature Made Melatonin 3mg",
                "url": "https://example.com/nature-made-melatonin",
                "snippet": "Best overall melatonin supplement. 3mg dose optimal for most adults. USP verified for purity.",
                "rating": 4.8,
                "price": "$12.99",
                "source": "HealthLine Best Melatonin 2024"
            },
            {
                "title": "Natrol Melatonin Fast Dissolve",
                "url": "https://example.com/natrol-melatonin",
                "snippet": "Fast-acting melatonin tablets. Strawberry flavor. 5mg strength for those who need higher dose.",
                "rating": 4.6,
                "price": "$9.99",
                "source": "Sleep Foundation Reviews"
            },
            {
                "title": "Life Extension Melatonin IR/XR",
                "url": "https://example.com/life-extension-melatonin",
                "snippet": "Dual-release formula for all-night sleep support. Combines immediate and extended release.",
                "rating": 4.7,
                "price": "$18.99",
                "source": "Consumer Reports"
            }
        ]
    else:
        # Generic wellness search results
        results = [
            {
                "title": f"Best {query} for Wellness",
                "url": f"https://example.com/{query.replace(' ', '-')}",
                "snippet": f"Top-rated {query} products reviewed by experts.",
                "rating": 4.5,
                "source": "Wellness Magazine"
            }
        ]
    
    return {
        "query": query,
        "results": results[:max_results],
        "total_results": len(results),
        "timestamp": datetime.now().isoformat(),
        "source": "web.search API"
    }