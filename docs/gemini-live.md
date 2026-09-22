# Veyra Voice — Gemini Live Integration Guide

## Overview

Veyra Voice integrates with Google's **Gemini Live API** (Bidirectional Streaming Content API) to conduct real-time, low-latency conversational voice phone calls with natural turn-taking, interruption handling, and continuous context tracking.

---

## Streaming Architecture

```
Phone / Browser Microphone
         │  (Audio: 8kHz μ-law or 16kHz PCM)
         ▼
    AudioPipeline
         │  (Normalized 16kHz PCM)
         ▼
  FastAPI WebSocket
         │
         ▼
 GeminiLiveProvider
         │  (Bidirectional WSS)
         ▼
Google Gemini Live Service (gemini-2.0-flash-exp)
         │  (Model Audio & Text Tokens)
         ▼
  FastAPI WebSocket
         │
         ▼
    AudioPipeline
         │  (Encoded for carrier format: G.711 μ-law)
         ▼
Phone Recipient / Browser Speaker
```

---

## Key Features

1. **System Instruction Injection**:
   The `GeminiLiveProvider` injects the campaign's target objective, customer persona directives, opening greeting, and question checklist into the session setup packet.
2. **Interruption Handling**:
   When the recipient speaks while the AI is outputting audio, the Gemini Live server emits an `interrupted: true` signal. The backend immediately stops audio playback and flushes downstream buffers.
3. **Structured Extraction via JSON Schema**:
   At the conclusion of the call, the `extract_structured_data` method transmits the complete conversation transcript back to the model with strict JSON schema constraints. The model extracts answers strictly without hallucinating or inventing unconfirmed details.
4. **Offline Development**:
   If `GEMINI_API_KEY` is not provided or `AI_PROVIDER=mock` is set, `MockAIProvider` simulates conversational turns, audio streaming, and structured extraction out of the box with zero external dependencies.
