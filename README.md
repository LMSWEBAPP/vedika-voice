# Veyra Voice — AI Outbound Voice Calling Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg?logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Proprietary-indigo.svg)]()

> An enterprise-grade, production-oriented AI outbound voice calling platform. Built with a clean layered architecture, provider abstractions for Gemini Live and carrier telephony (Exotel / Mock), real-time bidirectional audio streaming, structured script branching, lead CSV ingestion with DNC enforcement, and a modern dark SaaS dashboard with an in-browser live microphone testing studio.

---

## Key Features

- **Decoupled Provider Abstraction**:
  - `AIProvider`: Google **Gemini Live API** real-time bidirectional voice agent session & zero-key **MockAIProvider**.
  - `TelephonyProvider`: **Exotel** carrier integration & zero-key **MockTelephonyProvider**.
- **Structured Script Engine**:
  - Dialogue represented structurally with typed questions (`boolean`, `number`, `single_choice`, `rating`, `email`, `time`, etc.).
  - Conditional branching logic (e.g. `IF interested == true THEN ask team_size`).
- **Dedicated Audio Pipeline**:
  - Codec translation (8kHz G.711 μ-law) to AI linear PCM (16kHz / 24kHz), linear resampling, silence detection, and interruption handling.
- **In-Browser Voice Studio**:
  - Test voice conversations with the AI directly in your browser using your microphone and speakers before connecting carrier telephony.
- **Lead Management & Compliance**:
  - CSV file ingestion, automatic deduplication, E.164 phone normalization, and strict permanent **Do-Not-Call (DNC)** enforcement.
- **Structured Answer Extraction**:
  - Validates and stores structured conversational answers into database schemas without hallucination or missing data fabrication.
- **Modern Dark SaaS Dashboard**:
  - Responsive, glassmorphic UI with CSS design tokens, Recharts metrics trends, and complete call transcript inspection.

---

## Monorepo Layout

```
veyra-voice/
├── apps/
│   ├── web/                 # Next.js 14+ / React / TypeScript Dashboard
│   │   ├── app/             # App router pages (dashboard, campaigns, leads, calls, agent-builder)
│   │   ├── components/      # Reusable UI components & layouts
│   │   ├── features/        # Feature domain modules
│   │   ├── lib/             # API & WebSocket client
│   │   └── styles/          # Design tokens (variables.css, globals.css, components.css)
│   └── api/                 # FastAPI Python Backend
│       ├── app/
│       │   ├── api/v1/      # Thin routers (auth, campaigns, leads, calls, agents, analytics, webhooks)
│       │   ├── core/        # Config, database, security, logging, errors
│       │   ├── models/      # SQLAlchemy 2.0 async models
│       │   ├── repositories/# Database access layer
│       │   ├── services/    # Pure business logic layer
│       │   ├── providers/   # AI (Gemini Live/Mock) & Telephony (Exotel/Mock)
│       │   ├── agents/      # ConversationManager, ScriptEngine, DataExtractor
│       │   ├── telephony/   # AudioPipeline, CallSession
│       │   ├── websocket/   # Audio streaming & In-Browser tester sockets
│       │   └── workers/     # Campaign background batch runner
│       └── tests/           # Pytest test suite
├── packages/
│   └── shared-types/        # Shared TypeScript contracts
├── docs/                    # Complete architectural and API documentation
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   ├── gemini-live.md
│   ├── telephony.md
│   ├── security.md
│   └── deployment.md
├── scripts/
│   └── seed_database.py     # Rich demo campaigns, scripts, leads, and call logs
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Quick Start (Zero-Key Simulation Mode)

The entire platform runs out-of-the-box in simulation mode without requiring live carrier or Gemini credentials.

### 1. Backend Setup
```bash
# Install backend dependencies
pip install -r apps/api/requirements.txt

# Seed sample campaigns, structured scripts, leads, and call logs
python scripts/seed_database.py

# Launch FastAPI backend on port 8000
python -m uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

### 2. Frontend Dashboard Setup
```bash
# From repository root
npm run dev:web
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!

### Default Admin Login Credentials
- **Email**: `admin@veyravoice.com`
- **Password**: `admin123456`

---

## Running Automated Tests

```bash
python -m pytest apps/api/tests -v
```

---

## Switching to Production Gemini Live & Exotel

Set these environment variables in `.env`:
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

TELEPHONY_PROVIDER=exotel
EXOTEL_ACCOUNT_SID=your_exotel_account_sid
EXOTEL_API_KEY=your_exotel_api_key
EXOTEL_API_TOKEN=your_exotel_token
EXOTEL_CALLER_ID=+918012345678
EXOTEL_WEBHOOK_SECRET=your_hmac_webhook_secret
TELEPHONY_WEBHOOK_BASE_URL=https://api.yourdomain.com
```

---

## Documentation Links

- [Architecture & Design Decisions](docs/architecture.md)
- [Database Schema & Models](docs/database.md)
- [API Reference & WebSockets](docs/api.md)
- [Gemini Live Integration](docs/gemini-live.md)
- [Telephony & Carrier Abstraction](docs/telephony.md)
- [Security & Privacy](docs/security.md)
- [Deployment Guide](docs/deployment.md)
