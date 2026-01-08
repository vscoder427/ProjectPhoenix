# Claude Prompt – Rebuild Dave with Standards

This prompt should be fed to Claude before it starts any work on the Dave service so it produces an implementation that mirrors the current behavior and satisfies all Employa standards.

```
You are rebuilding the Dave service. Use the existing implementation and refreshed spec (docs/services/dave/spec.md) as your source of truth. Follow every requirement in ProjectPhoenix/docs/standards.

Use Python 3.12+ with FastAPI for the API layer, Pydantic v2 for data validation, and Loguru (or another structured JSON logger that is compatible with Google Cloud Logging) for production logging.

1. Project structure:
   * Match the service-template layout: api/, tests/, docs/, scripts/, Dockerfile, cloudbuild.yaml, Makefile, .env.example, README.md (ProjectPhoenix/docs/standards/service-template.md).
   * Include README sections (Overview, API Endpoints, Configuration, Local Development, Testing, Deployment, Runbook) with links to docs/spec.md and docs/runbook.md.

2. API surface:
    * Implement the health endpoints (`GET /`, `/health`, `/health/ready`, `/health/debug/prompts`) and guard them with the same readiness logic described in app/main.py.
    * Provide chat endpoints (POST /chat/message, GET /chat/stream, POST /chat/start, GET/DELETE /chat/conversations/{conversation_id}) with SSE semantics, guardrail enforcement, conversation ownership checks, rate-limit metadata, and knowledge/resource injection exactly as described in docs/services/dave/spec.md.
      - SSE responses must follow the format:
        ```
        event: {type}
        data: {json_payload}

        ```
        Valid event types are `message`, `token`, `resource`, `suggestion`, `error`, and `done`.
      - All error responses (including guardrail rejects, HTTPException hits, or Gemini failures) must follow RFC 7807 (Problem Details for HTTP APIs) with `type`, `title`, `status`, `detail`, and `instance` plus the request `correlation_id` value in the response body.
   * Implement knowledge endpoints (hybrid search, article/slug lookup, FAQ list, categories, recovery articles) plus admin prompt CRUD and nudge generation/batch/types endpoints as described in spec.

3. Authentication & guardrails:
   * Use X-API-Key + JWTs, differentiate admin vs normal keys (`verify_api_key`, `verify_admin_key`, `verify_user_or_admin`, `optional_auth`); never trust client-provided user_id on chat requests.
   * Guardrails must run in order: rate limiter, prompt injection detection, topic classifier. Rate limits (free/basic/premium/admin) must use Redis sorted sets when configured, fallback to in-memory otherwise.
   * Prompt injection patterns (ignore/disregard instructions, DAN/STAN/Omega, system prompt extraction, suspicious character ratio) and topic redirects (medical/therapy/legal/coding) must return friendly redirect copy instead of hitting Gemini.
   * Record guardrail metrics (`ai.token_count`, `ai.guardrail_blocked`) and include correlation IDs.

4. Dave core logic:
   * Conversation persistence uses ai_conversations + ai_messages tables in Supabase (client from app/clients/supabase.py).
   * PromptManager builds the system instruction (base, {user_type}_mode, recovery language, off-topic redirect), caches prompts for cache_ttl_prompts, and exposes methods for clearing cache on admin updates.
   * KnowledgeRepository loads storage bucket articles, caches semantic embeddings, supports hybrid search with semantic weight 0.65/fulltext 0.35, and exports recovery articles and FAQ metadata.
   * DaveChatService handles streaming/non-streaming responses, calls guardrails, saves user/assistant messages, emits `resource`, `token`, `suggestion`, `done`, and handles fallback responses when blocked.
   * NudgeService pulls prompts (falls back to fallback strings), builds Gemini prompt, enforces 100-200 char length, attaches CTA text/link from NUDGE_CTA_CONFIG, and returns fallback message if Gemini fails.
   * GeminiClient provides streaming, non-streaming, embeddings, circuit breaker (3 failures, 60s reset), and health check.

5. Testing + compliance:
   * Include pytest coverage of auth, chat, guardrails, health.
   * Document how prompt cache clearing, runbook steps, and CLI checklists meet the standards checklist (docs/services/dave/standards-checklist.md).
   * Provide runbook (docs/runbook.md) following the standards template including deploy/rollback/incident steps.

6. Deliverables:
   * README (per template) with links to spec/runbook/standards checklist.
   * Spec (per service-spec-template) with all sections populated.
   * Runbook capturing deploy/rollback/incident items plus monitoring notes (Gemini circuit breaker, guardrails, prompt cache, nudges).
   * Standards checklist and ADRs/decisions documenting compliance.
   * Mention the standards files referenced at the end of your output so reviewers can cross-check.

If anything in the current implementation conflicts with the standards, explain the conflict, how you resolved it, and note any follow-up actions (clear prompt cache, adjust runbook, etc.). Err on the side of clarity; more detail is better.
```

Feel free to reuse this prompt for future services by adjusting the service name and referenced spec/runbook.
