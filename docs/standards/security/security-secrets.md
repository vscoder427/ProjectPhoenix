# Security and Secrets Standard

This standard defines security and secrets management for all Employa microservices.

## Secrets Storage

- Use GCP Secret Manager for all runtime secrets
- Local development uses `.env` with no PHI
- Never commit secrets to the repo

> **Guidance:** use the [Secrets Access Policy](secrets-access-policy.md) when approving human review access or rotation requests.

## Service Identity

- Workload Identity is required
- Each service uses a dedicated service account with least privilege

## API Protection

- API Gateway auth required for external requests
- Service middleware enforces auth on all endpoints
- mTLS required for service-to-service calls

## Data Classification

- Formal data classification policy required (PHI, PII, internal, public)
- Data handling rules follow HIPAA compliance standard

## Key Rotation

- Automated secret rotation with audit trail
- Rotation schedules documented per secret

- Revoke service account keys and secrets immediately if SPIRE/Envoy reports identity anomalies; log in the incident tracker.
