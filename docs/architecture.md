# Veyra Voice — Architectural Blueprint

## System Overview

Veyra Voice is an enterprise-grade AI outbound voice calling platform engineered for high-concurrency conversational telephony, structured script execution, and real-time streaming AI voice agents.

The platform strictly enforces the **Separation of Concerns** principle:

```
[Web Dashboard (Next.js)]
        │
    HTTPS / WSS
        │
        ▼
[API Router (FastAPI v1)]
        │
        ▼
[Business Services]
        │
        ├─────────────────────────────┬───────────────────────────┐
        ▼                             ▼                           ▼
[Repositories]               [AIProvider Interface]      [TelephonyProvider Interface]
        │                             │                           │
        ▼                      ┌──────┴──────┐             ┌──────┴──────┐
   PostgreSQL / SQLite         │             │             │             │
                        GeminiLiveProvider MockAI      ExotelProvider MockTelephony
```

---

## Core Architectural Rules

1. **Provider Decoupling**: Business logic and campaign execution layers never invoke Google Gemini or Exotel directly. All external systems operate behind abstract interfaces (`AIProvider` and `TelephonyProvider`).
2. **Layered Isolation**:
   - `Router`: Pure HTTP & WebSocket deserialization and validation.
   - `Service`: Business rules, campaign workflows, extraction logic.
   - `Repository`: Database query formulation, transactions, and persistence.
   - `Database`: Normalized schema with foreign key integrity.
3. **Dedicated Audio Pipeline**:
   - `AudioPipeline` decouples codec translation (G.711 μ-law, 8kHz) and AI PCM audio formatting (16kHz / 24kHz) from application logic.
   - Silence detection and speech energy computation prevent race conditions and manage conversational interruptions.
4. **Deterministic Script Engine**:
   - Instead of feeding giant monolithic prompts to an LLM, the `ScriptEngine` structures dialogues into typed questions (`boolean`, `number`, `email`, `rating`, `single_choice`, etc.) and evaluates conditional branching (e.g. `IF interested == true THEN ask callback_time`).
5. **Zero-Key Offline Development Mode**:
   - The platform runs completely offline out-of-the-box using `AI_PROVIDER=mock` and `TELEPHONY_PROVIDER=mock`.
   - Real-world carrier calls and live Gemini sessions can be enabled simply by supplying environment variables.
