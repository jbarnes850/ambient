"""Mock APIs for health, calendar, and commerce data"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Any

class MockHealthAPI:
    """Mock health data API for demo purposes"""
    
    @staticmethod
    async def get_sleep_metrics(user_id: str) -> Dict[str, Any]:
        """Get mock sleep data for a user"""
        base_hours = 6.5
        variation = random.uniform(-1.5, 1.5)
        
        return {
            "user_id": user_id,
            "date": datetime.now().date().isoformat(),
            "hours": round(base_hours + variation, 1),
            "quality": round(random.uniform(0.6, 0.9), 2),
            "rem_sleep_minutes": random.randint(70, 120),
            "deep_sleep_minutes": random.randint(60, 100),
            "interruptions": random.randint(0, 3),
            "heart_rate_avg": random.randint(50, 65),
            "respiratory_rate": random.randint(12, 16)
        }
    
    @staticmethod
    async def get_activity_data(user_id: str) -> Dict[str, Any]:
        """Get mock activity data for a user"""
        return {
            "user_id": user_id,
            "date": datetime.now().date().isoformat(),
            "steps": random.randint(3000, 12000),
            "active_minutes": random.randint(15, 60),
            "calories_burned": random.randint(1800, 2500),
            "exercise_sessions": [
                {
                    "type": random.choice(["walking", "running", "yoga", "strength"]),
                    "duration_minutes": random.randint(20, 45),
                    "intensity": random.choice(["low", "moderate", "high"])
                }
            ],
            "sedentary_hours": round(random.uniform(6, 10), 1)
        }
    
    @staticmethod
    async def get_stress_metrics(user_id: str) -> Dict[str, Any]:
        """Get mock stress data for a user"""
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "stress_level": random.choice(["low", "moderate", "high"]),
            "heart_rate_variability": random.randint(30, 60),
            "recovery_score": round(random.uniform(0.5, 0.9), 2),
            "recommendations": [
                "Take a 5-minute breathing break",
                "Go for a short walk",
                "Practice mindfulness meditation"
            ]
        }
    
    @staticmethod
    async def get_hydration_data(user_id: str) -> Dict[str, Any]:
        """Get mock hydration data"""
        return {
            "user_id": user_id,
            "date": datetime.now().date().isoformat(),
            "water_intake_oz": random.randint(40, 80),
            "goal_oz": 64,
            "percentage_complete": round(random.uniform(0.6, 1.1), 2),
            "last_logged": (datetime.now() - timedelta(hours=random.randint(1, 3))).isoformat()
        }


class MockCalendarAPI:
    """Mock calendar API for demo purposes"""
    
    @staticmethod
    async def get_calendar_events(user_id: str) -> List[Dict[str, Any]]:
        """Get mock calendar events for today"""
        today = datetime.now().date()
        events = []
        
        # Morning standup
        events.append({
            "id": "evt-001",
            "title": "Team Standup",
            "start": f"{today}T09:00:00",
            "end": f"{today}T09:30:00",
            "type": "meeting",
            "recurring": True
        })
        
        # Random meetings throughout the day
        meeting_times = ["10:00", "11:00", "14:00", "15:30", "16:30"]
        for i, time in enumerate(random.sample(meeting_times, 3)):
            events.append({
                "id": f"evt-{i+2:03d}",
                "title": random.choice([
                    "Product Review", "1:1 with Manager", "Client Call",
                    "Sprint Planning", "Design Review", "Budget Meeting"
                ]),
                "start": f"{today}T{time}:00",
                "end": f"{today}T{time.split(':')[0]}:{int(time.split(':')[1]) + 30:02d}:00",
                "type": "meeting",
                "recurring": False
            })
        
        return sorted(events, key=lambda x: x["start"])
    
    @staticmethod
    async def analyze_schedule_density(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze calendar density and suggest optimizations"""
        meeting_hours = sum(
            (datetime.fromisoformat(e["end"]) - datetime.fromisoformat(e["start"])).seconds / 3600
            for e in events
        )
        
        return {
            "total_meetings": len(events),
            "meeting_hours": round(meeting_hours, 1),
            "density_score": round(meeting_hours / 8, 2),  # Assuming 8-hour workday
            "recommendations": [
                "Block 2pm-3pm for focused work" if meeting_hours > 4 else "Schedule looks balanced",
                "Consider making Team Standup async" if len(events) > 5 else "Good meeting distribution",
                "Add a 15-minute break after back-to-back meetings"
            ]
        }


class MockCommerceAPI:
    """Mock commerce API for wellness product searches"""
    
    @staticmethod
    async def search_wellness_products(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Mock product search results"""
        product_templates = [
            {
                "category": "sleep",
                "products": [
                    {"name": "Melatonin 5mg (60 tablets)", "price": 12.99, "rating": 4.5},
                    {"name": "Magnesium Glycinate 400mg", "price": 24.99, "rating": 4.7},
                    {"name": "Chamomile Tea (30 bags)", "price": 8.99, "rating": 4.3},
                    {"name": "Sleep Mask with Bluetooth", "price": 39.99, "rating": 4.6},
                    {"name": "White Noise Machine", "price": 49.99, "rating": 4.8}
                ]
            },
            {
                "category": "stress",
                "products": [
                    {"name": "Ashwagandha 600mg", "price": 19.99, "rating": 4.6},
                    {"name": "L-Theanine 200mg", "price": 16.99, "rating": 4.4},
                    {"name": "Stress Relief Essential Oil Blend", "price": 14.99, "rating": 4.5},
                    {"name": "Acupressure Mat", "price": 34.99, "rating": 4.3},
                    {"name": "Meditation App Annual Subscription", "price": 69.99, "rating": 4.7}
                ]
            },
            {
                "category": "hydration",
                "products": [
                    {"name": "Smart Water Bottle with Reminder", "price": 29.99, "rating": 4.4},
                    {"name": "Electrolyte Powder (30 servings)", "price": 22.99, "rating": 4.6},
                    {"name": "Himalayan Pink Salt", "price": 9.99, "rating": 4.5},
                    {"name": "Coconut Water (12 pack)", "price": 24.99, "rating": 4.3},
                    {"name": "Hydration Tracking App Premium", "price": 4.99, "rating": 4.2}
                ]
            }
        ]
        
        # Find relevant category based on query
        category = "sleep"  # default
        query_lower = query.lower()
        if "stress" in query_lower or "anxiety" in query_lower:
            category = "stress"
        elif "water" in query_lower or "hydrat" in query_lower:
            category = "hydration"
        
        products = next(cat["products"] for cat in product_templates if cat["category"] == category)
        
        # Add mock details to each product
        results = []
        for i, product in enumerate(products[:max_results]):
            results.append({
                "id": f"prod-{i+1:03d}",
                "name": product["name"],
                "price": product["price"],
                "rating": product["rating"],
                "reviews_count": random.randint(100, 5000),
                "in_stock": random.choice([True, True, True, False]),  # 75% in stock
                "prime_eligible": random.choice([True, True, False]),  # 66% prime
                "url": f"https://example.com/products/{i+1}",
                "description": f"High-quality {category} support product. {product['name']} helps with your wellness goals."
            })
        
        return results