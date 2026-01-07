# Golden Service Spec

## 1) Overview

- Service name: `golden-service-python`
- Business purpose: Demonstrate the canonical FastAPI service layout with observability, auth stub, and release readiness integration.
- Primary users: Platform engineers bootstrapping new services.
- Governance tier: Tier 0 (critical) for golden-template relevance.
- Owners: platform-ops@employa.work (primary), platform-automation@employa.work (backup).

## 2) Responsibilities

- Provide /health and /ready probes.
- Offer a starter `/api/v1/ping` endpoint plus metadata for instrumentation checks.
- Wrap request telemetry, structured logs, and OpenTelemetry instrumentation.

## 3) API Contract

- Base URL: `/api/v1/`
- Authentication: JWT via API Gateway (not implemented here).
- Endpoints:
  - `GET /health` -> `{"status":"ok"}`
  - `GET /ready` -> `{"status":"ready"}`
  - `GET /api/v1/ping` -> `{"status":"pong"}`
- Idempotency: GET endpoints only.

## 4) Data Model

- No persisted data yet.
- Schema ownership placeholder for future tables (per-service Postgres).

## 4.1) Compliance Flags

- HIPAA/PHI: no.
- GDPR/CCPA: yes (dto includes sample user metadata). DSAR lead: privacy@employa.work.
- Privacy standard: follow `privacy-gdpr-ccpa.md` for DSAR tracking.

## 5) Integrations

- Depends on Golden API Gateway, MemoryStore for caching, and SPIRE server for mTLS certificates.

## 6) Observability

- Metrics: `golden.requests`, `golden.latency`.
- SLO targets: 99.9% availability and <2% error rate; burn rate tracked in ownership checklist.
- Alerts: page on SLO breach, 5xx spikes >2%.

## 7) Security and Compliance

- Data classification: internal only.
- Access control: service account with least privilege; Workload Identity for GCP.
- Audit logging: structured JSON logs, request IDs.
- mTLS: Envoy sidecar with SPIRE; refer to `cloudrun-mtls-ops.md`.

## 8) Testing Strategy

- Contract tests via `schemathesis run docs/openapi/v1.yaml`.
- Unit tests with pytest/hypothesis.
- Lint: Ruff; Type: Pyright.

## 9) Runbook

- Deploy: run `make test`, `make contract`, build Docker image, run release checklist, and follow release readiness instructions.
- Rollback: redeploy last healthy revision from Cloud Run.
- Incident: use runbook checklist to page platform ops.

## 10) Open Questions

- Should future migrations expose GraphQL?
- Should there be a CRUD API for service metadata?
