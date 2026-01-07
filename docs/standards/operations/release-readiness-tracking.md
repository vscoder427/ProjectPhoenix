# Release Readiness Tracking

This document explains how release readiness checklists are generated, stored, and audited.

## Artifact Storage

- Each service repository keeps release checklists, scan output links, SBOMs, contract test reports, drift summaries, and config change logs in `docs/releases/<service-name>/<YYYY-MM-DD>-<release-tag>/`.
- Checklists are markdown files named `readiness.md` with front-matter describing service tier, release tag, and artifact list.
- Signed checklists, SBOMs, and security reports are referenced in the GitHub release body and stored in the release folder for auditing.

## Automation

- Use `scripts/build-release-checklist.ps1` (or equivalent) to gather results from CI artifacts, insert SLO burn-rate data, attach drift/config change summaries, and emit the checklist document before deployment.
- The script must fail the deploy gate if any required artifact is missing (lint, tests, SAST/SCA, SBOM, contract tests, guardrails per tier). Exceptions are documented in the [Standards Governance and Enforcement](standards-governance.md) policy and attached to the checklist.

## Human Review

- Manual approvers sign off by commenting `#ready` on the checklist issue and linking the entry to the release notes.
- Release readiness checklists are versioned (YYYY-MM-DD) so reviewers can compare edits across deployments.

## Audit Trail

- The release readiness folder is included in audit evidence packages (see [Compliance Audit Readiness](compliance-audit-readiness.md)) by pointing to the checklist, security scans, DSAR logs, and vendor/BAA evidence.
- For Tier 0 services, store extra documentation about disaster recovery drills, cost reviews, and vendor audits alongside the readiness checklist so handoffs see full readiness context.
