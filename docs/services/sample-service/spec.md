# Sample Service Spec

## 1) Overview
- Service name: `sample-service`
- Business purpose: expose a read/write scheduling API for cross-platform workforce automation
- Primary users: internal planners and scheduling agents
- Governance tier: Tier 1 (important)
- Primary owner: `@owner` (scheduling team), Backup owner: `@backup`
- On-call escalation: Scheduling pager -> Platform ops

## 2) Responsibilities
- In-scope: manage job creation, status tracking, notifications to downstream services
- Out-of-scope: payroll data, billing reconciliation

## 3) API Contract
- Base URL: `/api/v1/schedule`
- Authentication: Bearer JWT (gateway + service)
- Endpoints: GET `/jobs`, POST `/jobs`, PATCH `/jobs/:id`
- Idempotency: Client-provided `Idempotency-Key` for POST/PATCH

## 4) Data Model
- Owns `schedule` and `job_logs` tables in dedicated Postgres schema
- Retention: logs kept 90 days; schedule entries kept 1 year for audit
### 4.1) Compliance Flags
- HIPAA/PHI: no (low risk)
- GDPR/CCPA: yes (user profile info) – DSAR lead: `privacy@employa.work`
- Privacy sections: follow `privacy-gdpr-ccpa.md#DSAR`

## 5) Integrations
- Depends on Identity Gateway (100ms SLA), Notification Service (200ms)

## 6) Observability
- Metrics: `schedules.created`, `schedules.latency`
- SLO targets: 99.9% availability; burn-rate thresholds tracked in ownership checklist
- Alerts: page on 5xx > 2% sustained

## 7) Security and Compliance
- PHI/PII handling per HIPAA/Privacy standards
- Access controls via IAM roles and scoped service accounts
- Audit logging enabled with redaction per `logging-redaction.md`

## 8) Testing Strategy
- Contract tests via Schemathesis + `jobs` OpenAPI spec
- Integration tests cover Postgres + Notification API
- Load tests via k6 hitting `/jobs`

## 9) Runbook
- Deploy: build, scan, promote image, run readiness script, manual approve (see release-readiness.md)
- Rollback: redeploy last healthy revision via Cloud Run
- Incident: follow runbook templates for severity -> escalations

## 10) Open Questions
- Data residency for EU users (tracking in decision record)
- Polling/backpressure strategy (document in Decision Record Lite)
