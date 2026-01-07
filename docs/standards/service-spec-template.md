# Service Spec Template

Use this template to define the behavior and contract for each microservice.

## 1) Overview

- Service name
- Business purpose
- Primary users
- Governance tier (Tier 0/1/2) and applicable enforcement level
- Primary owner, backup owner, and on-call escalation path

## 2) Responsibilities

- In-scope responsibilities
- Explicit out-of-scope items

## 3) API Contract

- Base URL
- Authentication requirements
- Endpoints (method, path, request, response, errors)
- Idempotency requirements

## 4) Data Model

- Schema ownership
- Tables and key fields
- Retention requirements

## 4.1) Compliance Flags

- HIPAA/PHI scope (yes/no) and BAA references
- GDPR/CCPA scope and DSAR lead
- Privacy standard sections to follow

## 5) Integrations

- External dependencies
- SLAs and rate limits

## 6) Observability

- Metrics and SLO targets
- Logging and tracing requirements
- Alert burn-rate thresholds and dashboard links

## 7) Security and Compliance

- PHI/PII handling
- Access controls
- Audit logging
- HIPAA/PII scopes with reference to the HIPAA Compliance Standard
- GDPR/CCPA handling with link to the Privacy Standard

## 8) Testing Strategy

- Contract tests
- Integration tests
- Load tests

## 9) Runbook

- Deploy steps
- Rollback steps
- Incident response

## 10) Open Questions

- Risks and unknowns
- Link to the [Decision Record (Lite)](../templates/decision-record-lite.md) or `docs/decisions.md`
