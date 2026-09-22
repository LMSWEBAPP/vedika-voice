# Veyra Voice — Security & Privacy Architecture

## Security Principles

Security is treated as a first-class requirement across the architecture.

---

## 1. Secrets & Credentials Management
- Zero hardcoded secrets anywhere in the codebase.
- In production, secrets are ingested exclusively via environment variables (`.env`).
- Database and client responses never expose credentials, API keys, or raw JWT secrets.

## 2. Phone Number Masking & PII Protection
- Compliance with data privacy guidelines: phone numbers are masked in all application log streams:
  `mask_phone_number("+919876543210")` outputs `+91******3210`.
- Application logs never record bearer tokens, webhook signature secrets, or passwords.

## 3. Strict Do-Not-Call (DNC) Enforcement
- When a lead is marked `do_not_call = true`, the `SafetyGuard.check_dnc` method throws `DNCViolationError` immediately.
- The platform strictly rejects outbound call placement, campaign assignment, or automated retry for any flagged DNC contact.

## 4. Webhook Signature Verification
- Inbound carrier webhooks verify HMAC signatures against `EXOTEL_WEBHOOK_SECRET` before parsing payloads to prevent request spoofing.

## 5. Input Validation & Error Handling
- All external input is validated through Pydantic v2 and Zod schemas.
- Internal stack traces are suppressed in API responses to prevent information leakage. All errors are rendered in a standardized `{ error: { code, message, request_id } }` envelope.
