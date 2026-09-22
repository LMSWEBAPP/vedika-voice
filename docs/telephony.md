# Veyra Voice — Telephony Integration Guide

## Overview

All telephony carrier interactions in Veyra Voice are completely decoupled from application logic through the `TelephonyProvider` abstract interface.

---

## Telephony Architecture

```
[Campaign / Call Service]
           │
           ▼
   [TelephonyProvider]
           │
      ┌────┴────────────────────────┐
      ▼                             ▼
[MockTelephonyProvider]     [ExotelProvider]
(Zero-Key Simulation)       (Production Carrier)
      │                             │
      ▼                             ▼
Simulated Ringing &          Exotel REST API
Audio Loop                   (/v1/Accounts/{SID}/Calls/connect.json)
                                    │
                                    ▼
                             Carrier Telephony Network
```

---

## Providers

### 1. `MockTelephonyProvider` (Default for Local Development)
- Generates simulated call IDs (`mock_call_...`).
- Transitions calls through the realistic state machine:
  `INITIATING` -> `RINGING` -> `CONNECTED` -> `AI_GREETING` -> `IN_PROGRESS` -> `COMPLETED`.
- Allows end-to-end development, testing, and UI validation without an Exotel or carrier account.

### 2. `ExotelProvider` (Production Carrier)
- Uses Exotel's HTTP REST endpoints for outbound call placement.
- Supported configuration environment variables:
  - `EXOTEL_ACCOUNT_SID`
  - `EXOTEL_API_KEY`
  - `EXOTEL_API_TOKEN`
  - `EXOTEL_SUB_DOMAIN` (default `api.exotel.com`)
  - `EXOTEL_CALLER_ID`
  - `EXOTEL_WEBHOOK_SECRET`
- Verifies SHA256 HMAC signatures on inbound webhooks.
- Normalizes carrier states (`queued`, `ringing`, `in-progress`, `completed`, `busy`, `no-answer`) to platform `CallStatus` enums.
