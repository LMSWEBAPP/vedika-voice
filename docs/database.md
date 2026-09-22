# Veyra Voice — Database Schema & Data Models

## Entity Relationship Diagram (ERD)

```
[User] (1)
  │
  ├── (N) ──► [Campaign] (1)
  │             │
  │             ├── (1) ──► [CampaignScript]
  │             │
  │             └── (N) ──► [CampaignLead] (N) ◄── (1) [Lead]
  │                           │                         ▲
  │                           └── (N) ──► [Call] (1) ───┤
  │                                         │
  │                                         ├── (N) ──► [CallTranscript]
  │                                         ├── (N) ──► [CallAnswer]
  │                                         ├── (N) ──► [CallEvent]
  │                                         └── (N) ──► [AgentSession]
  │
  └── (N) ──► [Lead]
```

---

## Core Tables Specification

### 1. `users`
- `id` (VARCHAR 36, UUID, PK)
- `email` (VARCHAR 255, UNIQUE, INDEX)
- `hashed_password` (VARCHAR 255)
- `full_name` (VARCHAR 255, NULLABLE)
- `role` (VARCHAR 50, DEFAULT 'admin')
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)

### 2. `campaigns`
- `id` (VARCHAR 36, UUID, PK)
- `user_id` (VARCHAR 36, FK -> `users.id`)
- `name` (VARCHAR 255)
- `description` (TEXT, NULLABLE)
- `objective` (TEXT)
- `status` (VARCHAR 50, INDEX) — `DRAFT`, `SCHEDULED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`
- `primary_language` (VARCHAR 10, DEFAULT 'en')
- `fallback_language` (VARCHAR 10, DEFAULT 'en')
- `schedule_config` (JSON, NULLABLE)

### 3. `campaign_scripts`
- `id` (VARCHAR 36, UUID, PK)
- `campaign_id` (VARCHAR 36, FK -> `campaigns.id`, UNIQUE)
- `persona` (TEXT)
- `voice_name` (VARCHAR 50, e.g. 'Aoede', 'Puck', 'Charon')
- `opening` (TEXT)
- `objective` (TEXT)
- `questions` (JSON, List of typed questions with conditions)
- `closing` (TEXT)
- `fallback_response` (TEXT)
- `ai_disclosure` (TEXT)

### 4. `leads`
- `id` (VARCHAR 36, UUID, PK)
- `user_id` (VARCHAR 36, FK -> `users.id`)
- `phone` (VARCHAR 50, INDEX)
- `full_name` (VARCHAR 255, NULLABLE)
- `email` (VARCHAR 255, NULLABLE)
- `company` (VARCHAR 255, NULLABLE)
- `custom_data` (JSON, NULLABLE)
- `do_not_call` (BOOLEAN, DEFAULT FALSE, INDEX) — **Strict DNC Enforcement**

### 5. `campaign_leads`
- `id` (VARCHAR 36, UUID, PK)
- `campaign_id` (VARCHAR 36, FK -> `campaigns.id`)
- `lead_id` (VARCHAR 36, FK -> `leads.id`)
- `status` (VARCHAR 50, INDEX) — `NEW`, `QUEUED`, `CALLING`, `CONTACTED`, `INTERESTED`, `NOT_INTERESTED`, `CALLBACK`, `NO_ANSWER`, `INVALID`, `DO_NOT_CALL`
- `attempts` (INTEGER, DEFAULT 0)
- `last_called_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)

### 6. `calls`
- `id` (VARCHAR 36, UUID, PK)
- `campaign_id` (VARCHAR 36, FK -> `campaigns.id`)
- `lead_id` (VARCHAR 36, FK -> `leads.id`)
- `provider` (VARCHAR 50) — `mock`, `exotel`, `twilio`
- `provider_call_id` (VARCHAR 255, INDEX, NULLABLE)
- `status` (VARCHAR 50, INDEX) — `QUEUED`, `INITIATING`, `RINGING`, `CONNECTED`, `AI_GREETING`, `IN_PROGRESS`, `PAUSED`, `COMPLETED`, `FAILED`, `NO_ANSWER`, `BUSY`, `CANCELLED`
- `started_at`, `answered_at`, `ended_at` (TIMESTAMP WITH TIME ZONE)
- `duration_seconds` (INTEGER, DEFAULT 0)
- `language` (VARCHAR 10)
- `termination_reason` (VARCHAR 255)
- `recording_url` (VARCHAR 1000)

### 7. `call_transcripts`
- `id` (VARCHAR 36, UUID, PK)
- `call_id` (VARCHAR 36, FK -> `calls.id`)
- `speaker` (VARCHAR 20) — `ai`, `user`, `system`
- `text` (TEXT)
- `timestamp` (TIMESTAMP WITH TIME ZONE)
- `language` (VARCHAR 10)
- `confidence` (FLOAT, DEFAULT 1.0)
- `metadata_json` (JSON)

### 8. `call_answers`
- `id` (VARCHAR 36, UUID, PK)
- `call_id` (VARCHAR 36, FK -> `calls.id`)
- `question_id` (VARCHAR 100, INDEX)
- `question_text` (TEXT)
- `raw_answer` (TEXT)
- `extracted_value` (JSON)
- `is_valid` (BOOLEAN, DEFAULT TRUE)
- `confidence` (FLOAT, DEFAULT 1.0)
