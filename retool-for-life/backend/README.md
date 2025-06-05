# Ambient Backend

## Overview
FastAPI backend for the ReTool-for-Life meta-agent wellness platform. This service orchestrates AI agents that monitor health data, optimize schedules, and make wellness-related purchases on behalf of users.

## Architecture

### Core Components
- **main.py** - FastAPI application with REST endpoints and WebSocket support
- **orchestrator.py** - Meta-agent orchestrator for agent generation, evaluation, and RLAIF optimization
- **agents_sdk.py** - Wellness agent implementations using OpenAI Agents SDK
- **agents_whatsapp.py** - WhatsApp-specific agent implementations
- **tools.py** - Tool implementations (SMS, health metrics, calendar, commerce, web search)
- **tools/** - Modular tool implementations (communication, health, commerce, automation)
- **mock_apis.py** - Mock APIs for health, calendar, and commerce data
- **config.py** - Application configuration and settings

### API Endpoints
- `POST /api/users/{user_id}/generate-agent` - Generate personalized wellness agents
- `GET /api/users/{user_id}/agent-status` - Get agent status and performance metrics
- `POST /api/users/{user_id}/trigger-demo` - Run the complete demo sequence
- `POST /api/users/{user_id}/chat` - Chat with the active agent
- `WS /ws/{user_id}` - WebSocket for real-time updates

### Demo Workflow (PRD Requirements)
1. **09:00** - Pull sleep data → SMS recap → suggest meeting reschedule
2. **19:30** - SMS reminder about 22:00 screen-time lock
3. **22:00** - Lock distracting apps via iOS Shortcut
4. **22:05** - Web search for melatonin → SMS recommendation
5. **22:06** - Execute purchase if approved

## Setup

### Prerequisites
- Python 3.11+
- OpenAI API key
- Twilio account (optional, for real SMS)

### Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid  # Optional
TWILIO_AUTH_TOKEN=your_twilio_token  # Optional
TWILIO_PHONE_NUMBER=+1234567890      # Optional
DEMO_PHONE_NUMBER=+1234567890        # Demo recipient
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886  # Twilio Sandbox
HUMAN_WHATSAPP_NUMBER=whatsapp:+1234567890  # User's WhatsApp
TEXTBELT_API_KEY=your_textbelt_key  # Optional for SMS
```

### Running the Server
```bash
uvicorn main:app --reload --port 8000
```

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI app
├── orchestrator.py      # Meta-agent logic
├── agents_sdk.py        # SDK implementation
├── agents_whatsapp.py   # WhatsApp agents
├── tools.py             # Tool functions
├── tools/               # Modular tools
│   ├── communication.py
│   ├── health.py
│   ├── commerce.py
│   └── automation.py
├── mock_apis.py         # Mock data providers
├── config.py            # Settings
├── synthetic_users.json # Demo user profiles
└── requirements.txt     # Dependencies
```

### Adding New Tools
1. Implement the tool function in `tools.py`
2. Add tool definition to agent's `_get_tools()` method
3. Update tool execution mapping in `_execute_tool()`

### Testing
Run the demo sequence:
```bash
curl -X POST http://localhost:8000/api/users/demo-user-001/generate-agent
curl -X POST http://localhost:8000/api/users/demo-user-001/trigger-demo
```

## Key Features
- **Meta-Agent Orchestration** - Automatically generates and evaluates multiple agent variants
- **RLAIF Optimization** - Agents improve based on performance metrics
- **Real-time Updates** - WebSocket support for live agent actions
- **Approval System** - Human-in-the-loop for sensitive actions
- **Mock & Real Integrations** - Twilio for SMS, mocks for other services
