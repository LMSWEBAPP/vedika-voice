# AGENTS.md

## Project Philosophy

Build production-quality software, not disposable prototypes.

Priorities:

1. Correctness
2. Security
3. Maintainability
4. Modularity
5. Performance
6. UX

## Architecture

Use:

Frontend
→ API
→ Service
→ Repository
→ Database

External services must use provider abstractions.

Never directly couple business logic to:
- Gemini
- Exotel
- Twilio
- Redis
- Supabase

Use interfaces/adapters.

## Code Organization

Never create unnecessarily large files.

Prefer:

- one responsibility per module
- small functions
- reusable services
- typed interfaces
- dependency injection

Avoid:

- god classes
- god components
- duplicated logic
- circular dependencies
- magic values
- global mutable state

## Frontend

Use:
- TypeScript
- reusable components
- feature-based organization
- external CSS/CSS modules
- responsive design
- accessible components

Never place large CSS blocks inside JSX.

Never use inline styles for normal component styling unless dynamically required.

Every important UI must have:
- loading state
- empty state
- error state
- success state

## Backend

Use:
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- async I/O where appropriate

Routers must remain thin.

Business logic belongs in services.

Database access belongs in repositories.

External integrations belong in providers.

## Security

Never hard-code secrets.

Never commit:
- .env
- API keys
- passwords
- tokens
- private credentials

Validate all external input.

Use:
- authentication
- authorization
- rate limiting
- secure cookies
- webhook verification
- structured logging

Never log secrets or sensitive personal information.

Mask phone numbers in logs.

## AI

Never trust raw LLM output.

Validate structured output.

Never allow the AI to invent missing data.

Maintain explicit conversation state.

Use structured scripts instead of one giant prompt.

## Telephony

All telephony must go through:

TelephonyProvider

Initial implementation:

ExotelProvider

Development implementation:

MockTelephonyProvider

Never let campaign/business logic directly call Exotel.

## AI Provider

All AI functionality must go through:

AIProvider

Initial implementation:

GeminiLiveProvider

Development implementation:

MockAIProvider

## Testing

Every new feature should include appropriate tests.

Before marking work complete:

- run tests
- run lint
- run type checking
- verify error handling
- verify loading states
- verify responsive UI
- verify security implications

## Environment

All configuration comes from environment variables.

Provide `.env.example`.

Never hard-code credentials.

## Git

Use conventional commits.

Examples:

feat:
fix:
refactor:
security:
test:
docs:
chore:

## Before Coding

For every significant request:

1. Inspect existing files.
2. Understand existing architecture.
3. Identify reusable modules.
4. Plan the smallest clean implementation.
5. Implement.
6. Test.
7. Document.

Do not rewrite unrelated code.

## Definition of Done

A feature is not complete merely because the happy path works.

It must also handle:

- invalid input
- network failures
- provider failures
- authentication failures
- empty states
- loading states
- retries
- timeouts
- unexpected API responses
- security concerns

Keep the code clean, modular, secure, and easy for another developer to understand.