"""Automation tools for iOS shortcuts and web search"""

from typing import Dict, Any, Optional
from datetime import datetime


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