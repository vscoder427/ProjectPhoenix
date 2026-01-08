# Release Readiness Checklist

This standard defines a minimal release readiness checklist for production deploys and explains where supporting artifacts are tracked.

## Required Checks

- SLOs defined and alerts configured (or explicitly waived)
- Runbook updated with deploy and rollback steps
- Security scans (SAST/SCA/container) are green
- SBOM generated and stored
- Canary plan and rollback plan documented
- Post-deploy verification steps documented

## Artefact Tracking

- Every release gate artifact (SAST/SCA results, SBOM, security review checklist, telemetry changes, config diffs, drift reports, secret access approvals) is referenced in the release readiness checklist and stored in `docs/releases/<service>/YYYY-MM-DD/` or an equivalent release folder.
- Automate checklist generation via the `scripts/build-release-checklist.ps1` helper (create this script if it doesn't exist) that populates required entries and attaches it as a release asset before manual approval.
- Trigger the `.github/workflows/release-readiness.yml` workflow (either via `workflow_dispatch` or automatically on `release.published`) so CI runs the checklist builder, records the artifact path, and uploads it for auditors.
- The guardrail workflow (`pre-merge-guardrails.yml`) verifies the latest release-readiness run succeeded before allowing merges, creating an audit point for each release candidate.
- Document structured error reporting (error codes, severity, dashboards) in the release readiness artifacts and link back to the [Structured Error Reporting](structured-error-reporting.md) standard so every incident follows the schema.
- Post approval, publish release notes that link to the signed checklist, SBOM, and release folder described in the [Release Readiness Tracking](release-readiness-tracking.md) guide.

## Optional Checks (Tier 0 and 1 recommended)

- Load test baseline recorded
- Dependency updates reviewed within 30 days
- Incident drill completed within last quarter
