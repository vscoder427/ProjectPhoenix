# Dave Service Spec

- **Purpose:** FastAPI service that acts as Employa's conversational AI career coach, knowledge base gateway, admin prompt editor, and nudge generator. Serves human users over REST/SSE and machine clients (n8n, admin tooling) via authenticated API keys.
- **Deployment:** Packaged as a Docker image, runs on Cloud Run behind Kong/GCP API Gateway, exposes `/api/v1/*` plus `/docs` in non-production environments.
- **Tier/Owners:** Tier 1 (user-facing); primary owner `@ai-team`, backup `@platform-ops`.

## 2) Responsibilities
- Manage conversational state, persistence, and follow-up suggestions for every user interaction (Supabase `ai_conversations` + `ai_messages`).
- Protect the model with tiered rate limiting, prompt-injection detection, and topic classification before calling Gemini.
- Stream SSE responses (`/chat/stream`) and non-streaming replies (`/chat/message`) with knowledge base citations and follow-up prompts.
- Provide hybrid knowledge search that blends semantic (Gemini embeddings) and full-text results from Supabase storage/FAQ tables.
- Surface administrative workflows for prompt/version management with pagination, history, rollback, and cache controls.
- Generate nudge messages for n8n-driven workflows using specialized prompts, CTA templates, and Gemini-based text generation.
- Expose health/readiness instrumentation, Prometheus metrics, and correlation-aware structured logging.
- Gatekeepers: API key authentication (X-API-Key) and optional JWT bearer tokens via `employa_auth`, conversation-level authorization checks.

## 3) API Contract
### Base Settings
- **Base path:** `/api/v1`
- **Auth:** `X-API-Key` (service/admin) or `Authorization: Bearer <jwt>`; invalid credentials produce 401/403. Admin routes require `admin_api_key`.
- **CORS:** Origins read from `CORS_ORIGINS` env; middleware allows all headers/methods/credentials.

### Health
- `GET /` - basic status with service/version.
- `GET /health` - liveness probe (simple response).
- `GET /health/ready` - dependency check hitting Supabase and verifying Gemini config; returns 503 when a dependency fails.
- `GET /health/debug/prompts` - internal snippet showing prompt cache health and the full system prompt preview (uses `PromptManagerService`).

### Chat (`/chat`)
- `POST /chat/message` - standard message workflow; requires optional auth, enforces conversation ownership, runs guardrails, saves messages, returns response + resources/suggestions. Payload: `ChatMessageRequest`. Response: `ChatMessageResponse`.
- `GET /chat/stream` - SSE that streams tokens (`type=token`), knowledge resources (`type=resource`), suggestions (`type=suggestion`), and final event (`type=done`), or `type=error` when guardrails/model fail. Query params: `message`, optional `conversation_id`, `user_type` default `job_seeker`.
- `POST /chat/start` - creates a new conversation with welcome message built from prompts; returns welcome text and canned suggestions.
- `GET /chat/conversations` - paginated list of a user's conversations; requires authenticated user (JWT or non-admin API key); ensures user-only access.
- `GET /chat/conversations/{conversation_id}` - conversation detail with chronologically ordered messages; enforces authorized user/admin access.
- `DELETE /chat/conversations/{conversation_id}` - soft-archive conversation (updates status to `archived`) after owner or admin verification.

### Knowledge (`/knowledge`)
- `POST /knowledge/search` - hybrid/semantic/fulltext search (`SearchRequest`). Combines Supabase storage + FAQ data, returns `SearchResponse` sorted by normalized score, optionally includes full content.
- `GET /knowledge/articles/{article_id}` - fetch article metadata/content, increments view count.
- `GET /knowledge/articles/slug/{slug}` - slug-based article lookup.
- `GET /knowledge/faqs` - lists FAQs with filters (category, featured).
- `GET /knowledge/categories` - enumerates knowledge base categories.
- `GET /knowledge/recovery` - fetches recovery-focused articles limited by configurable keyword heuristics.

### Admin Prompts (`/admin/prompts`)
- `GET /admin/prompts` - paginated prompt listing (category filter, archive toggle); returns `PromptList`.
- `GET /admin/prompts/categories` - category counts.
- `GET /admin/prompts/{prompt_id}` - prompt detail with optional `?include_versions=true`.
- `PUT /admin/prompts/{prompt_id}` - create new prompt version, clears `PromptManagerService` cache.
- `POST /admin/prompts/{prompt_id}/rollback` - point-in-time rollback to an earlier version.
- `GET /admin/prompts/category/{category}` - all prompts within a category.
- `POST /admin/prompts/cache/clear` - flush prompt cache globally, per category, or per prompt.

### Nudges (`/nudges`)
- `POST /nudges/generate` - generates a Gemini-driven nudge for a single user; requires API key; enforces `_rate_limiter` (tokens ~150/request) before generation; returns `NudgeGenerateResponse`.
- `POST /nudges/generate/batch` - up to 50 nudges per call; rate-limited similarly; returns counts of succeeded/failed results.
- `GET /nudges/types` - returns available nudge types and trigger descriptions (mirrors `NudgeType` enum and `NUDGE_CTA_CONFIG` triggers).

## 4) Data Model
- **Supabase tables:**
  - `ai_conversations`: `id`, `user_id`, `title`, `status`, `context`, timestamps; soft delete via `status=archived`.
  - `ai_messages`: stores `role`, `content`, `metadata`, `resources`, `follow_up_suggestions` per message.
  - `admin_prompts` + `admin_prompt_versions`: versioned prompt storage with `current_version_id`.
  - `faqs`: question/answer catalog surfaced in knowledge search and resource injections.
- **Knowledge storage:** Supabase `knowledgebase` bucket contains `.html` articles parsed by `BeautifulSoup`; metadata cached once per runtime for search/context injection.
- **Prompt cache:** `PromptManagerService` caches prompts for `cache_ttl_prompts` seconds; `clear_cache` admin endpoint invalidates entries.
- **Rate limiting data:** `RateLimiter` persists per-user/IP usage in Redis sorted sets (minute/day windows) or in-memory fallback.

## 5) System Flow & Business Logic
- **Chat pipeline:** `DaveChatService.generate_response`/`stream_response` invoke guardrails (RateLimiter -> PromptInjectionDetector -> TopicClassifier), create/reuse conversation, save the user message, read recent history (limit 10), fetch knowledge resources, build the system prompt (base personality + user-type modes + recovery language + off-topic redirect), format history for Gemini, call Gemini (stream or not), surface follow-up suggestions, save the assistant message with `resources`/`suggestions`, and finally record tokens for rate limiting.
- **SSE output:** `stream_response` yields `StreamEvent` objects with event types `token`, `resource`, `suggestion`, `done`, and `error`. `resource` emits the `resources` list so frontends can show citations before tokens arrive.
- **Prompt manager:** composes system prompts from the `dave_system` category (`base_personality`, `{user_type}_mode`, `off_topic_redirect`) plus `recovery_language`; falls back to hardcoded personality/welcome copy when prompts are missing; caches each prompt for five minutes by default.
- **Guardrails:** `GuardrailsOrchestrator` orchestrates tiered rate limiting, prompt-injection detection (regexes for system override, jailbreak, suspicious characters), and topic classification (career keyword whitelist; polite redirects for medical/therapy/legal/coding). `record_request` counts tokens (chat uses ~2 tokens per word, nudges 150 tokens) in Redis/in-memory stores.
- **Knowledge search:** `KnowledgeRepository` caches storage articles/FAQs, generates Gemini embeddings, and implements `search_semantic`, `search_articles_fulltext`, `search_faqs_fulltext`, and `search_hybrid` (65% semantic weight, 35% fulltext). Results include `score`, `source`, `excerpt`, and optional `content`.
- **Nudge generation:** `NudgeService` pulls prompts from the `dave_nudges` category (fallback templates otherwise), injects context variables (user name, recovery stage, job/milestone info), enforces Gemini system instructions (100-200 characters, recovery-sensitive), trims outputs exceeding 300 characters, attaches CTA text/link from `NUDGE_CTA_CONFIG`, and returns metadata (`model`, `prompt_source`, `user_id`). The service also provides safe fallback messages when Gemini fails.
- **Gemini resilience:** `GeminiClient` supplies streaming/non-streaming generation plus embeddings, and a circuit breaker that opens after 3 consecutive failures, waits 60 seconds, and resets on success. Health checks use `GeminiClient.is_configured`.

## 6) Integrations
- **Upstream:** Kong/GCP API Gateway + Cloud Run handle routing, TLS, correlation ID headers (`X-Correlation-ID`, `X-Request-ID`, `X-Trace-ID`), and JWT propagation.
- **Downstream:**
  - **Supabase:** Postgres tables + storage bucket for prompts, conversations, FAQs, and articles.
  - **Google Gemini:** text generation (including SSE) and embeddings via `google.generativeai`.
  - **Redis (optional):** distributed rate limiting storage; service falls back to in-memory when unavailable.
  - **n8n workflows:** call `/nudges/generate` and `/nudges/generate/batch` with `X-API-Key`.
  - **employa_auth:** validates bearer JWTs so logged-in users can own conversations.
  - **httpx AsyncClient pool:** shared client fetches stored HTML articles for context/excerpt extraction.

## 7) Guardrails & Security
- **Authentication schemes:** `verify_api_key` distinguishes `dave` vs `admin` keys, `verify_admin_key` accepts either header or bearer token, `optional_auth` rejects invalid credentials and defaults to anonymous context, `verify_user_or_admin` requires JWT or admin key.
- **Conversation authorization:** `_enforce_conversation_access` only allows owners or admins to read/archive conversations; anonymous records are hidden from authenticated users.
- **Rate limiting:** tiered limits (free: 5 req/min, 100 req/day, 1k tokens/min; basic: 15/500; premium: 30/2000; admin: 100/10000) enforced before any Gemini call; `record_request` logs tokens (chat ~2 per word, nudges 150) for future checks.
- **Prompt injection detection:** `PromptInjectionDetector` blocks override/jailbreak/jailbreak patterns (ignore/disregard, roleplay, system prompt extraction, DAN/STAN/Omega, developer mode) and high special-character ratios, returning a friendly redirect copy.
- **Topic classification:** `TopicClassifier` allows requests that hit career keywords, redirects medical/therapy/legal/coding queries with curated messages, and labels greetings/general topics to keep Dave on-topic.
- **Gemini circuit breaker:** prevents repeated downstream failures by opening after three errors, logging `circuit_status`, and refusing new requests until the 60-second timeout elapses.
- **Logging:** `CorrelationIDMiddleware` injects IDs into every log entry, and production logs are JSON-formatted (via `python-json-logger`) while development uses readable formatting.

## 8) Observability & SLOs
- **Metrics:** `prometheus-fastapi-instrumentator` (if installed) exposes `/metrics`, instruments request latency, status codes, and in-flight requests (`dave_http_requests_inprogress`), and adds `dave_app_info` with version/env.
- **Health/readiness:** `/health/ready` runs Supabase/Solana (Gemini) checks; response includes per-dependency status and `503` when unhealthy.
- **SLO:** aim for 99.9% availability and <800ms time-to-first-token (p95); adversarial guardrail hits (prompt injection/redirect) are logged via `ai.guardrail_blocked`.

## 9) Testing
- **Pytest suite:** `api/tests` contains `test_auth.py`, `test_chat.py`, `test_guardrails.py`, and `test_health.py` covering authentication paths, SSE + non-streaming responses, guardrail detection messages, and dependency health.
- **Fixtures/config:** `conftest.py` wires FastAPI test client, mocked Gemini/Supabase clients, and resets the rate limiter between tests.
- **Schema coverage:** tests exercise Pydantic models (`ChatMessageResponse`, `SearchResponse`, `NudgeGenerateResponse`, `Prompt` list) to keep the OpenAPI schema honest.

## 10) Runbook
- **Circuit breaker alerts:** monitor logs/metrics for `Gemini circuit breaker: OPEN` warnings; wait 60s for reset or redeploy the Cloud Run revision if Gemini remains unresponsive.
- **Dependency failures:** `/health/ready` returning `not_ready` indicates Supabase/Gemini issues; platform ops should confirm credentials/endpoints and restart the service if needed.
- **Rate limiter fallback:** when Redis is unreachable, logs note the fallback to in-memory per-instance limits; expect short-lived limits and no distributed counters.
- **Prompt cache:** after bulk prompt changes, call `/admin/prompts/cache/clear` and optionally hit `/health/debug/prompts` to confirm system prompt assembly.
- **Nudge failures:** `/nudges/generate` returns curated fallbacks when Gemini/generation fails so downstream workflows still receive a message.
- **Rollbacks/deployments:** use Cloud Run revision rollback or redeploy; shared caches (prompt cache, knowledge embeddings) reset on startup.

