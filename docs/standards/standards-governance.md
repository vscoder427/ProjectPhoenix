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
- Tier-based enforcement uses the Service Tiering standard
- Guardrail workflow (`.github/workflows/pre-merge-guardrails.yml`) must pass on every PR; it validates the latest release-readiness run and ensures service specs/runbooks/README files exist before merging.
- CODEOWNERS and the PR template enforce required reviewers and checklist completion per tier before branch protection allows the merge.
- All public-facing text (UI, docs, alerts) should conform to the Language & Tone (Recovery Sensitive) standard to keep the brand voice unified.

## Branching and Commits

- Prefix feature branches with `feature/`, bug fixes with `fix/`, documentation changes with `docs/`, and refactors with `refactor/`.
- Commit messages must use Conventional Commits (`type(scope): summary`), where allowed types are `feat`, `fix`, `docs`, `style`, `refactor`, `test`, and `chore`.
- Add `!` for breaking changes; a scope is encouraged when it clarifies the impacted component or service.
- Outliers like hotfixes or experiments should still document their branch naming and commit rationale in STARTED.md or a short decision record.
