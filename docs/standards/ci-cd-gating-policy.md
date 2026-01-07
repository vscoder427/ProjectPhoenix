# CI/CD Gating Policy

This standard defines required checks for merge and deploy.

## Merge Gates

- Lint and formatting checks
- Type checking
- Unit and integration tests
- Security scans (SAST/SCA/container)
- Contract tests

## Deploy Gates

- SBOM generated and stored
- Signed image verified
- Canary rollout with health checks
- Deploy gate artifacts (scan reports, SBOM, canary metrics) must be attached to the release readiness checklist to provide reviewers a single source of truth.
