"""Communication tools for SMS and WhatsApp messaging"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import uuid
from twilio.rest import Client
from dotenv import load_dotenv

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


async def send_whatsapp(
    message: str,
    to_number: str,
    require_approval: bool = True
) -> Dict[str, Any]:
    """Send WhatsApp message via Twilio"""
    
    # Ensure WhatsApp format
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
    
    if require_approval:
        # Store in approval queue for demo
        approval_id = generate_approval_id()
        approval_queue[approval_id] = {
            "type": "whatsapp",
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
    
    # Send actual WhatsApp message if Twilio is configured
    if twilio_client:
        try:
            from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"
                
            message_obj = twilio_client.messages.create(
                body=message,
                from_=from_number,
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
            "message_sid": f"mock-wa-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "to_number": to_number,
            "note": "Twilio not configured - this is a mock WhatsApp response"
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
    elif action["type"] == "whatsapp":
        result = await send_whatsapp(
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


async def schedule_meeting(
    title: str,
    start_time: str,
    duration_minutes: int = 30,
    attendees: Optional[List[str]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Schedule a meeting (mock implementation)"""
    from mock_apis import MockCalendarAPI
    
    meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
    
    meeting = {
        "id": meeting_id,
        "title": title,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "attendees": attendees or [],
        "created_at": datetime.now().isoformat(),
        "status": "scheduled"
    }
    
    # In a real implementation, this would integrate with a calendar API
    return {
        "status": "success",
        "meeting": meeting,
        "message": f"Meeting '{title}' scheduled for {start_time}"
    }