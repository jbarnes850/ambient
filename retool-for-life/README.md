# ReTool-for-Life 🧬

**A meta-agent wellness platform that auto-generates personalized AI agents in one click**

ReTool-for-Life solves the "cold start" problem for wellness AI agents. Instead of requiring users to craft prompts or configure YAML files, our Meta-Agent automatically:

1. **Generates** multiple wellness agent variants based on your profile
2. **Evaluates** them against real-world scenarios
3. **Deploys** the best-performing agent instantly
4. **Self-improves** nightly using RLAIF (Reinforcement Learning from AI Feedback)

## 🏗️ Architecture

```bash
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│         (Real-time updates via WebSocket)                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Meta-Agent Orchestrator                 │   │
│  │     • Generates agent variants (Sleep, Stress, etc)  │   │
│  │     • Evaluates on test scenarios                    │   │
│  │     • Deploys best performer                         │   │
│  │     • RLAIF optimization loop                        │   │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            OpenAI Agents SDK + WhatsApp             │    │
│  │     • Real Twilio integration for messaging         │    │
│  │     • Mock APIs for Health, Calendar, Commerce      │    │
│  │     • Approval system for sensitive actions         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Twilio account (for WhatsApp/SMS)

### Backend Setup

```bash
cd retool-for-life/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - TWILIO_ACCOUNT_SID
# - TWILIO_AUTH_TOKEN
# - TWILIO_WHATSAPP_FROM (use Twilio sandbox: whatsapp:+14155238886)

# Run the backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd retool-for-life/frontend

# Install dependencies
npm install

# Run the frontend
npm run dev
```

Visit http://localhost:3003 to see the console.

## 🎮 Demo Workflow

Our agents execute a complete wellness workflow throughout the day:

| Time | Action | Tools Used |
|------|--------|------------|
| **09:00** | 📊 Analyze sleep data & suggest calendar optimization | WhatsApp, Health API, Calendar |
| **19:30** | ⏰ Remind about upcoming screen-time limits | WhatsApp |
| **22:00** | 📱 Lock distracting apps & dim screen | WhatsApp, iOS Shortcuts |
| **22:05** | 🔍 Search for best melatonin supplements | Web Search, Product Query |
| **22:06** | 🛒 Purchase approved items (sandbox mode) | Commerce API |
| **02:00** | 🧠 RLAIF optimization based on day's performance | Trace Analysis |

## 🔥 Key Features for Judges

1. **One-Click Setup**: No configuration needed - just select a user and click "Generate"
2. **Real-Time Visualization**: Watch agent generation, evaluation scores, and live actions
3. **WhatsApp Integration**: Real messaging via Twilio (not just mocks!)
4. **Approval System**: Human-in-the-loop for sensitive actions like purchases
5. **RLAIF Self-Improvement**: See the agent evolve based on performance metrics
6. **Complete Trace Visibility**: Every action is logged and viewable

## 📱 Demo Instructions

1. **Select User**: Choose "Sarah Chen" (WhatsApp-enabled profile)
2. **Generate Agent**: Click "Generate Wellness Agent" and watch the evaluation
3. **Run Demo**: Click "Run Demo Sequence" to see all 5 workflow steps
4. **Approve Actions**: Use the approval panel for purchases
5. **View Evolution**: Check performance metrics showing RLAIF improvements

## 🛠️ Tech Stack

- **Backend**: FastAPI, OpenAI Agents SDK, Twilio
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, WebSocket
- **AI Models**: GPT-4o (complex tasks), GPT-4o-mini (optimization)
- **Integrations**: WhatsApp (real), Health/Calendar/Commerce (mocked for demo)