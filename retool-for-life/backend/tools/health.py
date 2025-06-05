"""Health and wellness data tools"""

from typing import Dict, List, Any
from datetime import datetime
import json
import random
from mock_apis import MockHealthAPI, MockCalendarAPI


async def get_sleep_data(user_id: str) -> Dict[str, Any]:
    """Get sleep data for a user"""
    try:
        # Try to load from sleep_data.json if available
        try:
            with open("sleep_data.json", "r") as f:
                data = json.load(f)
                if user_id in data:
                    return data[user_id]
        except FileNotFoundError:
            pass
        
        # Otherwise use mock API
        return await MockHealthAPI.get_sleep_metrics(user_id)
    except Exception as e:
        return {"error": str(e)}


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