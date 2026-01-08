# Dave Service Runbook

This runbook mirrors the checklists in `ProjectPhoenix/docs/standards/operations/runbook-templates.md` while adding Dave-specific guidance (Gemini circuit breaker, guardrails, prompt cache, nudges).

## Deploy Checklist
- [ ] Build the Docker image via `Dockerfile` and `cloudbuild.yaml` (scan + vulnerability policies must pass).
- [ ] Deploy to staging/Cloud Run revision and wait for `/ready` to report `status: ready`.
- [ ] Run smoke tests: hit `GET /health`, `GET /health/ready`, `POST /chat/message` (mock user), `POST /knowledge/search`.
- [ ] Approve the production deploy after verifying SSE latency and `ai.token_count` is within expected bounds (refer to `app/main.py` instrumentation).
- [ ] Verify key endpoints (`/health`, `/ready`, `/chat/stream`, `/knowledge/search`, `/nudges/generate`) respond before routing traffic.

## Rollback Checklist
- [ ] Identify the last known good Cloud Run revision where `/ready` returned healthy status.
- [ ] Roll back the Cloud Run service to that revision and ensure the Gemini circuit breaker resets (watch logs for `Gemini circuit breaker: OPEN` warnings). The circuit breaker refuses requests after three failures and waits 60 seconds before retries.
- [ ] Confirm `/health/ready` shows all dependencies (Supabase, Gemini) as `ok` and monitor error rates/latency.

## Incident Checklist
- [ ] Declare a severity level in the internal incident tracking doc.
- [ ] Notify platform stakeholders, AI team, and compliance if sensitive data may have been exposed (PII resides in chat context and resources).
- [ ] Trace timeline by correlating `X-Correlation-ID` from requests (the middleware adds IDs to every log entry).
- [ ] Mitigate: scale Cloud Run CPUs, temporarily disable heavy features (e.g., knowledge search), or revert to a previous revision while Gemini recovers.
- [ ] Schedule a post-mortem and capture lessons learned in `docs/decisions.md`.

## Monitoring & Troubleshooting Notes
- **Gemini dependency:** circuit breaker lives in `app/clients/gemini.py`. When open, the service returns HTTP errors with `circuit breaker open`; wait 60s for reset or restart the service if Gemini is down for longer periods.
- **Rate limiter/guardrails:** check `ai.guardrail_blocked` metrics and logs from `app/guardrails`. Redis disconnects fall back to per-instance in-memory limits, so expect variability in token budgets but no shared state.
- **Structured errors:** Verify every incident log/error uses the RFC 7807 + [Structured Error Reporting](../standards/operations/structured-error-reporting.md) schema (`error.code`, `service.name`, `request.id`, `severity`) so alerts map cleanly to dashboards.
- **Prompt cache:** after prompt edits, call `POST /admin/prompts/cache/clear` (optionally filtered by category/name) to avoid stale instructions, then hit `/health/debug/prompts` to confirm the assembled system prompt.
- **Nudge errors:** `/nudges/generate` returns fallback messages (see `NudgeService._get_fallback_response`) if Gemini fails so downstream workflows can still notify users.

## Communication
- Mention impacted features (chat, knowledge, nudges) and whether `/chat/stream` tokens or SSE events were disrupted.
- Provide any relevant logs, screenshots from Prometheus/GCP monitoring, and updates to the standards checklist (`docs/standards-checklist.md`) if a deviation occurred.

Include this runbook in reviews and handoffs whenever Claude or other agents rebuild Dave to keep deployment/incident tooling aligned with the standards library.
