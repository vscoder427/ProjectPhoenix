# Dave Service Standards Checklist

This checklist tracks compliance with the Employa standards library so Claude can rebuild Dave with confidence.

## 1) Service template (`ProjectPhoenix/docs/standards/service-template.md`)
- **Required repo layout:** The Dave repo already follows the template (`api/`, `docs/`, `scripts/`, `Dockerfile`, `cloudbuild.yaml`, `.env.example`, `README.md`, etc.). Confirmed in `Dave/api/` and root-level artifacts.
- **Required endpoints:** The service exposes `/health` and `/ready` (see `app/main.py` health/readiness routers). ✅
- **Required README sections:** Not yet in `ProjectPhoenix/docs/services/dave/` because the README is missing; add `Overview`, `API Endpoints`, `Configuration`, `Local Development`, `Testing`, `Deployment`, and `Runbook` sections referencing the spec and runbook once written.
- **Required docs:** `docs/spec.md` exists and now adheres to the spec template below. `docs/runbook.md` is still pending—capture runbook run/rollback/alert steps per `operations/runbook-templates.md`. Also add `docs/adr/` records and link a small decision record (per the template checklist) once decisions are finalized.

## 2) Service spec template (`ProjectPhoenix/docs/standards/service-spec-template.md`)
The refreshed `spec.md` covers every numbered section:
  1. **Overview:** includes purpose, deployment, owners (`ProjectPhoenix/docs/services/dave/spec.md:1-6`).
  2. **Responsibilities:** lists conversation, guardrails, knowledge, prompts, nudges, observability (`spec.md:7-15`).
  3. **API Contract:** details base settings plus health/chat/knowledge/admin/nudge endpoints with auth and SSE events (`spec.md:17-58`).
  4. **Data Model:** Supabase tables, storage bucket, cache, rate-limit data (`spec.md:59-64`).
  5. **Integrations:** upstream/downstream dependencies are enumerated (`spec.md:69-78`).
  6. **Observability:** metrics, health, SLOs are clearly documented (`spec.md:97-103`).
  7. **Security and Compliance:** guardrails, authentication, circuit breaker, logging are spelled out (`spec.md:88-96`).
  8. **Testing Strategy:** summarizes pytest suites and schema coverage (`spec.md:102-105`).
  9. **Runbook:** describes circuit breaker, dependency failures, rate limiter fallback, prompt cache, nudge fallbacks, rollbacks (`spec.md:107-113`).
 10. **Open Questions:** currently none—add this section if any inquiry remains.

## 3) Next steps for Claude
1. **Add the missing README** (`ProjectPhoenix/docs/services/dave/README.md`) to narrate the required sections and link `spec.md` and the forthcoming runbook.
2. **Create `docs/runbook.md`** using the runbook template and capture the rollback/dependency alerts already described in `spec.md:107-113`.
3. **Document ADRs/decisions** under `docs/adr/` or via the decision-record-lite template so Architecture reviewers can trace trade-offs (`ProjectPhoenix/docs/standards/service-template.md: Required Docs`).
4. **Maintain `spec.md` compliance:** keep each numbered section aligned with the service spec template whenever code/functionality evolves.

If you’d like, I can also help bootstrapping the runbook or README sections referenced here so Claude can focus on generating the implementation rather than recreating documentation from scratch.
