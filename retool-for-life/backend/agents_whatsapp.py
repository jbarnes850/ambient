"""WhatsApp-based wellness agent integration"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from agents import WellnessAgent, AgentResponse, ToolCall
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
import logging

load_dotenv()

# WhatsApp configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox default

# Initialize Twilio client if credentials available
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logging.warning(f"Could not initialize WhatsApp client: {e}")


class WhatsAppWellnessAgent(WellnessAgent):
    """WhatsApp-based wellness agent that uses WhatsApp instead of SMS"""
    
    def _generate_instructions(self) -> str:
        """Generate WhatsApp-specific instructions"""
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        You are a WhatsApp-based wellness assistant that:
        - Communicates exclusively through WhatsApp messages
        - Manages sleep tracking and optimization
        - Controls screentime limits and app restrictions
        - Provides timely wellness reminders
        
        For WhatsApp messages, use the send_whatsapp tool instead of send_sms.
        
        Demo workflow tasks:
        - At 09:00: Pull sleep data, send WhatsApp recap, ask about moving tomorrow's 7:30 AM meeting
        - At 19:30: Send WhatsApp heads-up about 22:00 screentime limits
        - At 22:00: Send WhatsApp notification and activate screentime limits/shortcuts
        """
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Override to include WhatsApp-specific tools"""
        tools = super()._get_tools()
        
        # Add WhatsApp tool
        tools.append({
            "type": "function",
            "function": {
                "name": "send_whatsapp",
                "description": "Send a WhatsApp message to the user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send via WhatsApp"
                        },
                        "to_number": {
                            "type": "string",
                            "description": "WhatsApp number (optional, uses user profile)"
                        }
                    },
                    "required": ["message"]
                }
            }
        })
        
        # Add screentime control tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "start_screentime_limit",
                    "description": "Send notification about upcoming screentime limits",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "activate_screentime",
                    "description": "Activate screentime limits and app restrictions",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_productivity_shortcut",
                    "description": "Run shortcut to dim screen and disable distracting apps",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shortcut_type": {
                                "type": "string",
                                "enum": ["bedtime", "focus", "morning"],
                                "description": "Type of productivity shortcut to run"
                            }
                        },
                        "required": ["shortcut_type"]
                    }
                }
            }
        ])
        
        return tools
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute WhatsApp-specific tools"""
        
        if tool_name == "send_whatsapp":
            return await self._send_whatsapp(
                arguments.get("message"),
                arguments.get("to_number", self.user_profile.get("whatsapp_number", self.user_profile.get("phone")))
            )
        
        elif tool_name == "start_screentime_limit":
            message = "Heads‐up: At 10 PM tonight, screentime limits on Reddit and X will activate."
            return await self._send_whatsapp(message)
        
        elif tool_name == "activate_screentime":
            message = "Screentime is now ON. Your distracting apps have been limited."
            result = await self._send_whatsapp(message)
            # Also trigger the shortcut
            shortcut_result = await self._execute_tool("run_productivity_shortcut", {"shortcut_type": "bedtime"})
            return {
                "whatsapp_result": result,
                "shortcut_result": shortcut_result
            }
        
        elif tool_name == "run_productivity_shortcut":
            shortcut_type = arguments.get("shortcut_type", "bedtime")
            shortcuts = {
                "bedtime": "Shortcut executed: distracting apps turned off, brightness dimmed.",
                "focus": "Shortcut executed: notifications silenced, focus apps enabled.",
                "morning": "Shortcut executed: brightness increased, morning apps enabled."
            }
            return {
                "status": "executed",
                "shortcut_type": shortcut_type,
                "result": shortcuts.get(shortcut_type, "Unknown shortcut type")
            }
        
        # Fallback to parent implementation
        return await super()._execute_tool(tool_name, arguments)
    
    async def _send_whatsapp(self, message: str, to_number: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        
        if not to_number:
            to_number = self.user_profile.get("whatsapp_number", self.user_profile.get("phone"))
        
        # Ensure WhatsApp format
        if to_number and not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        if twilio_client and to_number:
            try:
                msg = twilio_client.messages.create(
                    body=message,
                    from_=TWILIO_WHATSAPP_FROM,
                    to=to_number
                )
                return {
                    "status": "sent",
                    "message_sid": msg.sid,
                    "channel": "whatsapp",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e),
                    "channel": "whatsapp"
                }
        
        # Mock response if Twilio not configured
        return {
            "status": "sent_mock",
            "message": message,
            "channel": "whatsapp",
            "to": to_number,
            "timestamp": datetime.now().isoformat(),
            "note": "WhatsApp not configured - mock response"
        }


class WhatsAppSleepAgent(WhatsAppWellnessAgent):
    """Specialized WhatsApp agent for sleep optimization with screentime control"""
    
    def _generate_instructions(self) -> str:
        base_instructions = super()._generate_instructions()
        return base_instructions + """
        
        As a WhatsApp Sleep Specialist, you focus on:
        - Tracking and analyzing sleep patterns
        - Managing evening screentime limits
        - Sending bedtime reminders via WhatsApp
        - Controlling device settings for better sleep
        
        Your daily routine:
        - Morning (9:00 AM): Analyze last night's sleep, suggest calendar optimizations
        - Evening (7:30 PM): Warn about upcoming screentime limits
        - Bedtime (10:00 PM): Activate screentime limits and sleep mode
        """
    
    async def morning_routine(self) -> Dict[str, Any]:
        """Execute morning wellness check via WhatsApp"""
        
        # Get sleep data
        sleep_data = {
            "last_night": {"duration_hours": 5, "quality": "light—woke up 3 times"},
            "goal": {"target_hours": 8, "advice": "Wind down 30 minutes before bed; avoid screens after 10 PM."}
        }
        
        # Compose morning message
        message = f"""Good morning! Sleep recap:
• Duration: {sleep_data['last_night']['duration_hours']} hours
• Quality: {sleep_data['last_night']['quality']}

To reach your {sleep_data['goal']['target_hours']}-hour goal:
- Move tomorrow's 7:30 AM meeting to a later slot
- Enable screentime limits at 10 PM tonight

{sleep_data['goal']['advice']}"""
        
        # Send via WhatsApp
        send_result = await self._send_whatsapp(message)
        
        # Ask about meeting
        meeting_prompt = "Do you approve moving tomorrow's 7:30 AM 1:1 to a later time? Reply YES or NO."
        meeting_result = await self._send_whatsapp(meeting_prompt)
        
        return {
            "sleep_recap": send_result,
            "meeting_request": meeting_result,
            "sleep_data": sleep_data
        }