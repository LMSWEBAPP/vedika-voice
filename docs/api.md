# Veyra Voice — API Reference Specification

Base URL: `http://localhost:8000/api/v1`

All responses follow standard HTTP codes and uniform error structures:

```json
{
  "error": {
    "code": "DO_NOT_CALL_VIOLATION",
    "message": "Phone number is on the permanent Do-Not-Call (DNC) list.",
    "request_id": "c7a8...",
    "details": { "phone": "+919888877777" }
  }
}
```

---

## Endpoints

### 1. Health Checks
- `GET /health`: Overall system readiness and version.
- `GET /health/database`: Database connection test.
- `GET /health/ai`: Active AI provider (`mock` or `gemini`).
- `GET /health/telephony`: Active telephony provider (`mock` or `exotel`).

### 2. Authentication
- `POST /auth/register`: Register admin/operator user.
- `POST /auth/login`: Authenticate and receive signed JWT access token.
- `GET /auth/me`: Current user profile.

### 3. Campaigns
- `GET /campaigns`: List campaigns with lead counts and progress percentages.
- `POST /campaigns`: Create campaign with embedded script.
- `GET /campaigns/{id}`: Detailed campaign info including script and questions.
- `PUT /campaigns/{id}`: Update campaign metadata.
- `POST /campaigns/{id}/status`: Transition status (`ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`).
- `PUT /campaigns/{id}/script`: Update structured questions, persona, and greetings.
- `POST /campaigns/{id}/start`: Launch campaign batch execution.
- `POST /campaigns/{id}/pause`: Pause campaign.
- `POST /campaigns/{id}/stop`: Stop campaign.

### 4. Leads
- `GET /leads`: Paginated lead query with text search and DNC filtering.
- `POST /leads`: Create individual lead with duplicate check.
- `GET /leads/{id}`: Fetch single lead.
- `PUT /leads/{id}`: Update lead details.
- `POST /leads/{id}/dnc`: Toggle Do-Not-Call flag (`?do_not_call=true|false`).
- `POST /leads/upload-csv`: Multipart CSV upload with automatic deduplication, phone normalization, and DNC detection.
- `POST /leads/assign`: Batch assign leads to a target campaign.
- `GET /leads/campaign/{campaign_id}`: List leads assigned to specific campaign.

### 5. Calls
- `GET /calls`: List all calls with status, campaign, and duration filters.
- `POST /calls/initiate`: Trigger outbound call for a lead in a campaign.
- `GET /calls/{id}`: Full call inspection: transcripts, structured answers, events.
- `POST /calls/{id}/retry`: Schedule retry for unanswered or failed call.

### 6. Analytics
- `GET /analytics/overview`: Aggregated stats: total leads, calls made, answered, completed, conversion rate, average duration, 7-day trend, and language distribution.

### 7. Webhooks
- `POST /webhooks/telephony/call-status`: Carrier webhook endpoint with HMAC signature verification and idempotent state updates.

### 8. WebSockets
- `WS /ws/agent/test/{campaign_id}`: Real-time browser audio & text testing socket.
- `WS /ws/telephony/media/{call_id}`: Carrier audio media stream socket.
