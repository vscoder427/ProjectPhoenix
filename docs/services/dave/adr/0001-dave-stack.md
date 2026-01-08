# Decision Record (Lite) – Dave Service Stack

## Decision
- The Dave service will be implemented as a FastAPI application hosted on Cloud Run, integrating directly with Google Gemini (for generation + embeddings) and Supabase (Postgres + storage bucket) while enforcing guardrails/rate limiting before calling any LLM.

## Options Considered
- **Option A:** Keep the previous monolithic service (if any) without the new guardrail stack. Rejected for lacking modern guardrail coverage and SSE streaming.
- **Option B:** Switch to a different conversational platform (e.g., a managed workflow or chatbot framework). Rejected due to platform familiarity and the need for fine-grained guardrail control.

## Decision Criteria
- Alignment with platform standards (Cloud Run, Kong API Gateway).
- Ability to enforce guardrails (rate limiting, prompt injection, topic classification).
- Observability (Prometheus metrics, correlation IDs, structured logs).
- Reuse of existing infrastructure (Gemini, Supabase, Supabase storage).

## Chosen Option and Rationale
- **Decision:** FastAPI service with `app/api/v1` routers backed by Gemini and Supabase, augmented by guardrail services.
- **Rationale:** FastAPI already powers the current Dave implementation, gives us direct control over SSE streaming, integrates with the existing Prometheus instrumentation, and lets us add guardrails/ rate limits before hitting Gemini. Gemini’s circuit breaker plus Supabase’s vector store satisfy the semantic search needs.

## Follow-ups
- Keep this decision updated if the service migration ever considers a different LLM, storage backend, or host environment.
