# Enterprise Architecture Principles

This document captures long-term engineering guardrails for Employa microservices. It is the default standard for all new builds and rebuilds.

## Scalability and Performance

- Services are stateless and horizontally scalable on Cloud Run (autoscale only).
- Define SLOs per service with error budgets and targets (p95 latency, availability, error rate).
- Shared cache uses MemoryStore (Redis) for cross-instance consistency.
- Background work runs in Cloud Tasks (no long-running work in request paths).
- Enforce rate limiting at API Gateway with per-key quotas and backpressure.

## Reliability and Resilience

- Provide /health and /ready endpoints.
- Standardized timeouts, retries with jitter, and circuit breakers for external calls.
- Implement idempotency for all write endpoints.
- Gracefully degrade with safe fallback responses when dependencies fail.
- Automated rollback on SLO breach with last known good Cloud Run revision.

## Security and Privacy

- Secrets stored only in GCP Secret Manager.
- Least-privilege DB roles per service and isolated schemas.
- Auth enforced at API Gateway and in service middleware.
- SAST + SCA + container scanning required in CI.
- Audit logs for all auth events and data mutation actions.
- Data retention and deletion policies documented per service.

## Compatibility and Evolution

- Version all public APIs with a compatibility matrix.
- Deprecation window is 180 days with migration guides.
- Use expand/contract migrations with compatibility tests.
- Contract testing is a required compatibility gate.
- Event payloads are versioned with a schema registry.

## Operational Excellence

- Standard CI/CD pipeline with automated deploys and canary rollouts.
- Runbooks include deployments, incidents, rollbacks, and on-call escalation.
- Full observability (metrics, tracing, dashboards).
- Cost budgets and alerts per service.
- Release notes and post-deploy verification checklists required.

## Data Architecture

- Each service owns its schema and migrations.
- Cross-service access only via APIs (no shared DB access).
- Migration contracts required per service.
- Pub/Sub with schema registry and DLQ for events.
- Standard data retention with legal hold and deletion verification.

## Engineering Workflow

- TDD required for all changes.
- PR review required with CI gates.
- Definition of Done includes tests, docs, security checks, and operational readiness (runbook + rollout/rollback plan).
- ADRs required for architectural changes.
- Trunk-based development with release tags and changelog.
