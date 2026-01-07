# Standards Governance and Enforcement

This standard defines how standards are created, updated, and enforced.

## Ownership

- Standards have an owner and backup owner
- Ownership is listed in each standard when practical

## Versioning

- Standards are versioned by date (YYYY-MM-DD)
- Breaking changes require a migration plan and timeline

## Change Process

- Changes require an ADR or a brief rationale section in the PR
- Security, compliance, and platform owners must review
- Announce changes and effective dates in release notes

## Exceptions and Waivers

- Exceptions require written justification and an end date
- Approvals by security and platform owners are required
- Exceptions are tracked and reviewed quarterly

## Enforcement

- Branch protection on `main`
- Required reviewers for standards changes
- Required checks: lint, type check, tests, security scans, SBOM, contract tests
- Production deploys require manual approval
