# Sample Service README

## Overview

- Purpose: schedules and dispatches internal jobs for workforce automation.
- Tier: Tier 1 (important) per [Service Tiering](../standards/service-tiering.md).
- Owners: Primary `@owner`, Backup `@backup`, On-call scheduling + platform ops.
- Privacy: This service handles PII, so follow `[Privacy (GDPR/CCPA)](../standards/privacy-gdpr-ccpa.md)` and see the [Service Spec](spec.md) compliance flags.

## Local Development

- Start Postgres via `docker-compose`.
- Copy `.env.example` to `.env` and load secrets from Secret Manager (via Workload Identity).
- Run `./scripts/start.sh` (example) to launch FastAPI + Envoy sidecar locally.

## Testing

- Unit/integration tests: `pytest tests/`.
- Contract tests: `schemathesis run docs/openapi/v1.yaml`.
- Run `scripts/build-release-checklist.ps1 -ServiceName sample-service -ReleaseTag dev` before pushing to staging to populate readiness artifacts.

## Release

- Follow the [Release Readiness Checklist](../standards/release-readiness.md) and link artifacts into `docs/releases/sample-service/<date>` (per [Release Readiness Tracking](../standards/release-readiness-tracking.md)).
- Ensure SBOM, security scans, and drift reports are attached to the checklist and included in release notes.
- Document new decision records in `docs/decisions.md` (can use the [Decision Record (Lite)](../templates/decision-record-lite.md)).

## Ownership & Handoff

- Ownership checklist in README:

```
Primary: @owner
Backup: @backup
On-call: platform ops
Monthly: SLO review, burn rate, cost anomaly, runbook refresh
```

- Track knowledge transfer items as specified in the [Service Ownership Checklist](../templates/service-ownership-checklist.md).
