# Dave Service Spec

## 1) Overview
- **Service Name:** `dave`
- **Business Purpose:** Unified AI Career Coach & Gateway. Handles all conversational AI, prompt management, and knowledge base retrieval.
- **Tier:** Tier 1 (Important - User Facing).
- **Owners:** `@ai-team` (Primary), `@platform-ops` (Backup).

## 2) Responsibilities
- **In-Scope:**
  - AI Conversation state management (Supabase).
  - Prompt injection guardrails & rate limiting.
  - Streaming responses (SSE) to frontend.
  - Knowledge base vector search (RAG).
- **Out-of-Scope:**
  - User auth (handled by Identity Gateway).
  - Raw job data scraping (handled by CareerIntelligence).

## 3) API Contract
- **Base URL:** `/api/v1/`
- **Auth:** `Authorization: Bearer <jwt>` (validated by Gateway + middleware).
- **Endpoints:**
  - `POST /chat/message` - Send user message, get AI response.
  - `GET /chat/stream` - SSE endpoint for real-time tokens.
  - `GET /knowledge/search` - Semantic search for career articles.
  - `GET /admin/prompts` - Internal admin for prompt versioning.

## 4) Data Model
- **Database:** Dedicated `dave` schema in Supabase.
- **Tables:** `ai_conversations`, `ai_messages`, `admin_prompts`, `faqs`.
- **Retention:**
  - Chat logs: 1 year (User Visibility).
  - Prompts: Permanent (Versioned).

## 5) Integrations
- **Upstream:** API Gateway (Kong/GCP).
- **Downstream:**
  - Google Gemini Pro (LLM).
  - Supabase Vector Store.

## 6) Observability
- **SLOs:**
  - Availability: 99.9%.
  - Latency (Time to First Token): < 800ms (p95).
- **Metrics:** `ai.token_count`, `ai.guardrail_blocked`.

## 7) Security & Compliance
- **PHI:** None (Career coaching only).
- **PII:** Usernames/resumes in context. Redacted in logs.
- **Guardrails:** Input validation for prompt injection required before LLM call.

## 8) Testing
- **Contract:** Schemathesis against OpenAPI.
- **Integration:** Mocked Gemini responses.
- **Safety:** Semantic fuzzing for jailbreaks.

## 9) Runbook
- **Rollback:** Revert Cloud Run revision.
- **Dependency Failure:** If Gemini is down, fallback to "Maintenance Mode" static response.
