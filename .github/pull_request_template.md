# PR Checklist

## Standards Level

**Select the appropriate standards level for this change:** (See [Service Development Workflow](docs/guides/service-development-workflow.md#standards-levels-minimal-moderate-full))

- [ ] **Minimal Standards** (Simple fix: < 50 lines, 1 file, basic tests)
- [ ] **Moderate Standards** (Multi-file, new endpoint, comprehensive tests)
- [ ] **Full Standards** (Architectural change, breaking change, 85% coverage, full release readiness)

---

## Minimal Standards (Required for All PRs)

- [ ] Basic tests added for changes (happy path + error case)
- [ ] Linting passed: `ruff check app/`
- [ ] Formatting applied: `ruff format app/`
- [ ] Conventional commit format used in PR title (`fix:`, `feat:`, `docs:`, `refactor:`, `test:`)
- [ ] Issue referenced: `Closes #X` or `Fixes #X`

## Moderate Standards (Required if 2+ files changed or API modified)

- [ ] Comprehensive tests (unit + integration) with good coverage
- [ ] Service docs updated:
  - [ ] `docs/services/<service>/spec.md` (if API/behavior changed)
  - [ ] `docs/services/<service>/runbook.md` (if operational procedures changed)
  - [ ] `README.md` (if setup/usage changed)
- [ ] OpenAPI spec updated (if API endpoints changed)
- [ ] `CHANGELOG.md` updated
- [ ] ADR created if significant design decision made

## Full Standards (Required for Architectural/Security/Breaking Changes)

- [ ] **85%+ test coverage achieved:** `pytest --cov=app --cov-fail-under=85`
- [ ] **ADR created:** `docs/services/<service>/adr/XXXX-title.md` for architectural decisions
- [ ] **Release Readiness Checklist generated** via `scripts/build-release-checklist.ps1` (see `docs/standards/release-readiness.md`)
- [ ] **SBOM + security scan summaries** attached to `docs/releases/<service>/<tag>/`
- [ ] **Contract testing:** Schemathesis tests for API changes
- [ ] **Security scans passed:** Bandit (SAST), Trivy (container)
- [ ] **Performance testing:** k6 load tests for user-facing changes
- [ ] **Observability goals, SLOs, and runbook notes** referenced in release artifacts
- [ ] **Release notes drafted** in `docs/releases/<service>/<tag>/notes.md`
- [ ] **Breaking change documented** (if applicable): Migration guide included
- [ ] **PR includes required reviewers** per tier (Tier 0 + Tier 1 require platform/security sign-off)

---

## Summary

**Closes:** #[issue-number]

Describe the change and pull in any relevant links (spec, ticket, decision record, etc.).

## Testing Summary

[Describe tests added/updated, coverage achieved, and any manual testing performed]

**Coverage:** __%

## Documentation Updated

- [ ] Inline code comments (if logic changed)
- [ ] Service spec.md
- [ ] Runbook.md
- [ ] README.md
- [ ] ADR created
- [ ] CHANGELOG.md
- [ ] N/A - No documentation changes needed
