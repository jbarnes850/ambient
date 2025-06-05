#!/Users/gabefish/whatsapp-agent-clean/venv/bin/python
import os
import json
import asyncio
import time
import logging
import requests  # For TextBelt SMS

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], check=True)
    from dotenv import load_dotenv
    load_dotenv()

# Install required packages if not already installed
try:
    from agents import Agent, function_tool, Runner
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "openai-agents"], check=True)
    from agents import Agent, function_tool, Runner

# Install Twilio SDK if missing
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "twilio"], check=True)
    from twilio.rest import Client as TwilioClient

# (Optional) If running in a Jupyter/Colab environment, enable async event loop nesting
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION & LOGGING
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    force=True
)

# These must be set beforehand (e.g., in Colab via %env):
#   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
#   HUMAN_WHATSAPP_NUMBER, OPENAI_API_KEY

TWILIO_ACCOUNT_SID    = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN     = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM  = os.getenv("TWILIO_WHATSAPP_FROM")   # e.g. "whatsapp:+14155238886"
HUMAN_WHATSAPP_NUMBER = os.getenv("HUMAN_WHATSAPP_NUMBER")  # e.g. "+12675744122" or "whatsapp:+12675744122"
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")

# TextBelt configuration
TEXTBELT_API_KEY = "f8bc4da08cae40cef83ea15c86a90054cbe58ba4ZS6PF51oFdHbMtxKZacIefamQ"

missing = [
    name for name, val in [
        ("TWILIO_ACCOUNT_SID", TWILIO_ACCOUNT_SID),
        ("TWILIO_AUTH_TOKEN", TWILIO_AUTH_TOKEN),
        ("TWILIO_WHATSAPP_FROM", TWILIO_WHATSAPP_FROM),
        ("HUMAN_WHATSAPP_NUMBER", HUMAN_WHATSAPP_NUMBER),
        ("OPENAI_API_KEY", OPENAI_API_KEY),
    ] if not val
]
if missing:
    raise RuntimeError(f"Missing environment variable(s): {', '.join(missing)}")

# Ensure proper "whatsapp:" prefixes
if not TWILIO_WHATSAPP_FROM.startswith("whatsapp:"):
    TWILIO_WHATSAPP_FROM = "whatsapp:" + TWILIO_WHATSAPP_FROM
if not HUMAN_WHATSAPP_NUMBER.startswith("whatsapp:"):
    HUMAN_WHATSAPP_NUMBER = "whatsapp:" + HUMAN_WHATSAPP_NUMBER

# Extract phone number for SMS (remove whatsapp: prefix)
SMS_PHONE_NUMBER = HUMAN_WHATSAPP_NUMBER.replace("whatsapp:", "")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize Twilio client
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

SLEEP_DATA_PATH = "sleep_data.json"
if not os.path.isfile(SLEEP_DATA_PATH):
    sample_sleep = {
        "last_night": {"duration_hours": 5, "quality": "light—woke up 3 times"},
        "goal":       {"target_hours": 8, "advice": "Wind down 30 minutes before bed; avoid screens after 10 PM."}
    }
    with open(SLEEP_DATA_PATH, "w") as f:
        json.dump(sample_sleep, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# PLAIN HELPER FUNCTIONS (Called directly at 7:30 PM & 10 PM)
# ──────────────────────────────────────────────────────────────────────────────

def send_whatsapp_text(message: str) -> str:
    """
    Sends a WhatsApp message via Twilio, retrying up to 3 times if there is an error.
    Returns a summary string.
    """
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            msg = twilio_client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP_FROM,
                to=HUMAN_WHATSAPP_NUMBER
            )
            logging.info(f"Twilio WhatsApp SID {msg.sid} (status={msg.status})")
            return f"Sent WhatsApp (SID: {msg.sid}, status: {msg.status})"
        except Exception as e:
            logging.warning(f"Attempt {attempt} → Twilio error: {e}")
            time.sleep(2)
    return "Error sending WhatsApp: exceeded retry attempts"


def send_textbelt_sms(message: str) -> str:
    """
    Sends an SMS via TextBelt API.
    Returns a summary string.
    """
    try:
        response = requests.post('https://textbelt.com/text', {
            'phone': SMS_PHONE_NUMBER,
            'message': message,
            'key': TEXTBELT_API_KEY,
        })
        result = response.json()
        
        if result.get('success'):
            logging.info(f"TextBelt SMS sent successfully: {result}")
            return f"Sent SMS via TextBelt (success: {result.get('success')})"
        else:
            error_msg = result.get('error', 'Unknown error')
            logging.error(f"TextBelt SMS failed: {error_msg}")
            return f"Error sending SMS: {error_msg}"
    except Exception as e:
        logging.error(f"TextBelt SMS exception: {e}")
        return f"Error sending SMS: {e}"


def start_screentime_limit_action() -> str:
    """
    Sends a WhatsApp notification that screentime limits activate at 10 PM.
    """
    message = "Heads‐up: At 10 PM tonight, screentime limits on Reddit and X will activate."
    result = send_whatsapp_text(message)
    logging.info(f"start_screentime_limit_action → {result}")
    return result


def activate_screentime_action() -> str:
    """
    Sends a WhatsApp notification that screentime is now ON.
    """
    message = "Distracting apps are now limited, brightness is dimmed. Alarm for 8:00AM is set!"
    result = send_whatsapp_text(message)
    logging.info(f"activate_screentime_action → {result}")
    return result


def send_sleep_mode_sms() -> str:
    """
    Sends "SLEEP_MODE_ON" SMS via TextBelt at 10 PM.
    """
    result = send_textbelt_sms("SLEEP_MODE_ON")
    logging.info(f"send_sleep_mode_sms → {result}")
    return result


def run_shortcut_action() -> str:
    """
    Simulates the shortcut that turns off distracting apps and dims brightness.
    """
    result = "Shortcut executed: distracting apps turned off, brightness dimmed."
    logging.info(f"run_shortcut_action → {result}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# AGENT-EXPOSED TOOL FUNCTIONS (only for 9:00 AM via the Agent)
# ──────────────────────────────────────────────────────────────────────────────

@function_tool
def get_sleep_data(path: str) -> dict:
    """
    Reads the user's sleep data from a JSON file.
    Returns a dict with the parsed contents.
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
        logging.info(f"get_sleep_data → {data}")
        return data
    except Exception as e:
        logging.error(f"get_sleep_data error: {e}")
        return {"error": f"Failed to load sleep data: {e}"}


@function_tool
def send_text(message: str) -> str:
    """
    Wrapper around send_whatsapp_text, exposed to the Agent as a FunctionTool.
    """
    return send_whatsapp_text(message)


@function_tool
def ask_move_meeting() -> str:
    """
    Sends a WhatsApp prompt asking approval to move the 7:30 AM 1:1 tomorrow.
    Does NOT read or echo the user's reply.
    """
    prompt = "Do you approve moving tomorrow's 7:30 AM 1:1 to a later time? Reply YES or NO."
    send_result = send_whatsapp_text(prompt)
    logging.info(f"ask_move_meeting → sent prompt, got: {send_result}")
    return send_result


# ──────────────────────────────────────────────────────────────────────────────
# SET UP "ORCHESTRATOR" AGENT (Only Runs at 9:00 AM)
# ──────────────────────────────────────────────────────────────────────────────

orchestrator_agent = Agent(
    name="OrchestratorAgent",
    model="gpt-4o-mini",
    instructions="""
You are a daily health‐and‐productivity assistant, and you only run at 9:00 AM:

1. Call get_sleep_data("sleep_data.json").
2. Compose a message that:
     • Notes last night's sleep duration and quality.
     • Says: "To reach 8 hours tomorrow night:
         – Move the 7:30 AM 1:1 tomorrow to an available slot.
         – Set an 8:00 AM alarm for tomorrow.
         – Enable screentime limits at 10 PM tonight."
3. Call send_text with exactly that message.
4. Call ask_move_meeting() to send the "move meeting" prompt.

Do NOT attempt to validate or echo the user's reply.
""",
    tools=[get_sleep_data, send_text, ask_move_meeting]
)


# ──────────────────────────────────────────────────────────────────────────────
# ASYNCHRONOUS "AUTOMATED TIME" PROMPTS
# ──────────────────────────────────────────────────────────────────────────────

async def main():
    print("\n🚀 Demo: Automatically triggering 9:00 AM, 7:30 PM, and 10:00 PM events 🚀\n")

    # 1) Simulate 9:00 AM via the Agent
    print("\n[Trigger] EVENT_9AM\n")
    result_9am = await Runner.run(orchestrator_agent, "EVENT_9AM")
    print("→ Agent result (9AM):", result_9am, "\n")

    # Wait 10 seconds
    print("⏰ Waiting 10 seconds before 7:30 PM event...\n")
    await asyncio.sleep(10)

    # 2) Simulate 7:30 PM by calling start_screentime_limit_action() directly
    print("\n[Trigger] Direct call: start_screentime_limit_action()\n")
    result_730pm = start_screentime_limit_action()
    print("→ start_screentime_limit_action result:", result_730pm, "\n")

    # Wait 10 seconds
    print("⏰ Waiting 10 seconds before 10:00 PM event...\n")
    await asyncio.sleep(10)

    # 3) Simulate 10:00 PM by calling activate_screentime_action(), send_sleep_mode_sms() & run_shortcut_action()
    print("\n[Trigger] Direct call: activate_screentime_action(), send_sleep_mode_sms() & run_shortcut_action()\n")
    result_10pm_msg = activate_screentime_action()
    print("→ activate_screentime_action result:", result_10pm_msg)
    result_10pm_sms = send_sleep_mode_sms()
    print("→ send_sleep_mode_sms result:", result_10pm_sms)
    result_10pm_shortcut = run_shortcut_action()
    print("→ run_shortcut_action result:", result_10pm_shortcut, "\n")

    print("\n✅ All steps complete. ✅\n")


# Run the demo
if __name__ == "__main__":
    asyncio.run(main())
