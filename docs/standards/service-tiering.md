# Service Tiering and Required Standards

This standard defines service tiers and which standards are required for each tier.

## Tier Definitions

- Tier 0 (critical): auth, PHI/PII, payments, or core platform services
- Tier 1 (important): user-facing services without direct PHI/PII storage
- Tier 2 (low risk): internal tools, batch jobs, or non-critical services

## Required Standards by Tier

### Tier 0 (critical)

- Enterprise Architecture Principles
- API Conventions
- Security and Secrets
- Privacy (GDPR/CCPA)
- HIPAA Compliance (if PHI)
- Data Classification and Retention
- Auth and JWT
- DB Isolation and Migration Contracts
- Logging and Observability
- SLO and Alerting Templates
- Runbooks and Incident Response
- CI/CD and Deployment
- CI/CD Gating Policy
- Supply Chain and SBOM
- Build Provenance
- Threat Modeling

### Tier 1 (important)

- Enterprise Architecture Principles
- API Conventions
- Security and Secrets
- Privacy (GDPR/CCPA) if PII
- Data Classification and Retention
- Auth and JWT
- DB Isolation and Migration Contracts
- Logging and Observability
- Runbooks and Incident Response
- CI/CD and Deployment
- CI/CD Gating Policy

### Tier 2 (low risk)

- API Conventions (if public)
- Security and Secrets
- Privacy (GDPR/CCPA) if PII
- Data Classification and Retention (if PII)
- CI/CD and Deployment

## Tier Changes

- Tier changes require an ADR or written approval
- Tier 0 cannot be downgraded without security review
