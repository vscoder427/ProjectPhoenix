# Release Readiness Checklist

This standard defines a minimal release readiness checklist for production deploys.

## Required Checks

- SLOs defined and alerts configured (or explicitly waived)
- Runbook updated with deploy and rollback steps
- Security scans (SAST/SCA/container) are green
- SBOM generated and stored
- Canary plan and rollback plan documented
- Post-deploy verification steps documented

## Optional Checks (Tier 0 and 1 recommended)

- Load test baseline recorded
- Dependency updates reviewed within 30 days
- Incident drill completed within last quarter
