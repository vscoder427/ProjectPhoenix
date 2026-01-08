# Dave Service Overview

## Overview
- Dave is Employa’s conversational AI career coach. The service exposes FastAPI endpoints for chat (SSE + non-streaming), knowledge search, admin prompt management, and nudge generation. It acts as a gateway to Google Gemini, Supabase, and the knowledge base bucket while enforcing guardrails (rate limits, prompt injection, topic classification) on every request. This README links back to the canonical spec (`docs/spec.md`) and runbook (`docs/runbook.md`) documented in the service standards library.

## API Endpoints
- **Base path:** `/api/v1`
- **Health & readiness:** `GET /`, `GET /health`, `GET /health/ready`, `GET /health/debug/prompts`
- **Chat:** `POST /chat/message`, `GET /chat/stream`, `POST /chat/start`, `GET /chat/conversations`, `GET /chat/conversations/{conversation_id}`, `DELETE /chat/conversations/{conversation_id}`
- **Knowledge:** `POST /knowledge/search`, `GET /knowledge/articles/{article_id}`, `GET /knowledge/articles/slug/{slug}`, `GET /knowledge/faqs`, `GET /knowledge/categories`, `GET /knowledge/recovery`
- **Admin prompts:** `GET /admin/prompts`, `GET /admin/prompts/categories`, `GET /admin/prompts/{prompt_id}`, `PUT /admin/prompts/{prompt_id}`, `POST /admin/prompts/{prompt_id}/rollback`, `GET /admin/prompts/category/{category}`, `POST /admin/prompts/cache/clear`
- **Nudges:** `POST /nudges/generate`, `POST /nudges/generate/batch`, `GET /nudges/types`
- All endpoints require `X-API-Key` (admin or service scopes) or a JWT bearer token; admin-only endpoints also accept the admin key via bearer.

## Configuration
- Copy `Dave/api/.env.example` to `.env` and populate the following environment variables:
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`
  - `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`
  - `DAVE_API_KEY`, `ADMIN_API_KEY`
  - Optional: `REDIS_URL` (rate limiting), `CORS_ORIGINS`, `RATE_LIMIT_ENABLED`
  - Standard runtime knobs: `HOST`, `PORT`, `APP_ENV`, `DEBUG`, `LOG_LEVEL`, `CACHE_TTL_PROMPTS`
- Settings are centralized in `api/app/config.py`, which exposes helpers such as `settings.is_production`, `is_development`, and the computed `cors_origins_list`.

## Local Development
1. `cd Dave/api`
2. `python -m venv .venv && . .venv/Scripts/Activate.ps1` (or `source .venv/bin/activate`)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in the required secrets (Supabase service key, Gemini API key, etc.).
5. Launch the service with `uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`
6. Visit `http://localhost:8080/docs` while in development mode to explore OpenAPI docs.

## Testing
- Run `pytest` from `Dave/api/tests`; the suite covers auth middleware, chat flows (streaming + non-streaming), guardrail detectors, and health endpoints.
- Use `requirements.lock` to pin transitive dependencies before running in CI/emulator environments.
- Contract testing (Schemathesis) and safety fuzzing are encouraged by the standards, but the existing stack relies on the pytest coverage mentioned above.

## Deployment
- Build the Docker image with the root `Dockerfile` (wraps `Dave/api/Dockerfile` via the `cloudbuild.yaml` pipeline).
- Deploy through Cloud Build and Cloud Run using `cloudbuild.yaml`; ensure the same env vars are provided in the Cloud Run service settings and that `/ready` and `/health` endpoints are healthy before routing traffic.
- GitHub Actions/Cloud Build should scan the image, run smoke tests, and verify key endpoints as described in `docs/standards/operations/runbook-templates.md`.
- Monitor `Gemini circuit breaker`, rate limiter metrics (`ai.guardrail_blocked`), and SSE latency to meet the documented SLOs (99.9% availability, <800ms first token).
- Errors must follow RFC 7807 and the [Structured Error Reporting](../standards/operations/structured-error-reporting.md) schema so dashboards can correlate `error.code`, `request.id`, and severity.

## Runbook
- See `docs/runbook.md` for the deploy/rollback/incident checklists tailored to Dave. The runbook references the same guidance as `docs/standards/operations/runbook-templates.md` and includes notes on Gemini dependency failures, prompt cache commands (`/admin/prompts/cache/clear`), and the fallback messaging behavior exposed in `/nudges`.

## Related Docs
- **Service spec:** `docs/spec.md`
- **Runbook:** `docs/runbook.md`
- **Standards checklist:** `docs/standards-checklist.md`
- **Decision log:** `docs/decisions.md`
