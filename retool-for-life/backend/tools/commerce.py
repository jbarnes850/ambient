"""Commerce and shopping tools"""

from typing import Dict, List, Any
from datetime import datetime
import uuid
from mock_apis import MockCommerceAPI
from .communication import generate_approval_id, approval_queue


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