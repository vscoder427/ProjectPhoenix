# Developer Quick Reference

Copy this checklist into your PR description or use it while working on an issue.

## Pre-Implementation

- [ ] Issue selected and understood
- [ ] Complexity assessed: ☐ Simple ☐ Moderate ☐ Complex
- [ ] Standards level determined: ☐ Minimal ☐ Moderate ☐ Full
- [ ] Dependencies identified (no blockers)
- [ ] Branch created: `fix/issue-{num}-{desc}` or `feat/issue-{num}-{desc}`
- [ ] Local environment working (`pytest` passes, service starts)
- [ ] Pre-commit hooks installed (see First-Time Setup below)

## Implementation

- [ ] Tests written (TDD preferred)
- [ ] Code changes completed
- [ ] Code follows [Coding Conventions](../standards/coding-conventions.md)
- [ ] Functions < 50 lines
- [ ] Type hints used (Pydantic models)
- [ ] No hardcoded secrets
- [ ] No PHI/PII in logs
- [ ] Error handling uses HTTPException

## Testing

- [ ] All tests pass: `pytest`
- [ ] New tests added for changes
- [ ] Coverage checked: `pytest --cov=app --cov-report=term-missing`
- [ ] Manual testing performed

**Coverage achieved:** __%

## Code Quality

- [ ] Linting passed: `ruff check app/`
- [ ] Formatting applied: `ruff format app/`
- [ ] Type checking (optional for minimal): `mypy app/`

## Documentation

- [ ] Inline comments updated (if logic changed)
- [ ] README.md updated (if setup/usage changed)
- [ ] Service spec.md updated (if API/behavior changed)
- [ ] Runbook.md updated (if operational procedures changed)
- [ ] ADR created (if architectural decision made)
- [ ] CHANGELOG.md updated

## Pull Request

- [ ] PR title uses conventional commit: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`
- [ ] Breaking change uses `!`: `feat!:` or `fix!:`
- [ ] Issue referenced: "Closes #X" or "Fixes #X"
- [ ] PR description includes:
  - [ ] Summary of changes
  - [ ] Standards level (minimal/moderate/full)
  - [ ] Testing performed
  - [ ] Documentation updated
- [ ] Reviewers assigned

## Complexity-Specific Items

### If Moderate or Full:
- [ ] Comprehensive tests (unit + integration)
- [ ] Service spec.md updated
- [ ] OpenAPI spec updated (if API changed)
- [ ] CHANGELOG.md updated

### If Full (Architectural/Security/Breaking):
- [ ] 85% test coverage achieved: `pytest --cov=app --cov-fail-under=85`
- [ ] ADR written: `docs/services/{service}/adr/XXXX-title.md`
- [ ] Release readiness checklist generated: `.\scripts\build-release-checklist.ps1`
- [ ] Security scan passed: Bandit, Trivy
- [ ] Contract tests added: Schemathesis
- [ ] Performance tested: k6 (if user-facing)
- [ ] SBOM attached to release artifacts

### If HIPAA/Security Change:
- [ ] Security review checklist completed
- [ ] Threat model reviewed
- [ ] PHI handling verified (encryption, RLS, logging redaction)
- [ ] Secrets in GCP Secret Manager only
- [ ] BAA verification (if vendor involved)

## Post-Merge

- [ ] CI/CD pipeline passed
- [ ] Branch deleted (local and remote)
- [ ] Deployment verified (if auto-deployed)
- [ ] Issue automatically closed via "Closes #X"
- [ ] Monitoring checks (if production change)

---

## First-Time Setup

**Install pre-commit hooks (required for all developers):**

```bash
# One-time installation
pip install pre-commit detect-secrets
pre-commit install
pre-commit install --hook-type commit-msg

# Verify installation
pre-commit run --all-files
```

Pre-commit hooks will:
- Block commits containing secrets/credentials
- Enforce conventional commit messages
- Check for merge conflicts and large files

See [security/security-scanning.md](../standards/security/security-scanning.md) for full security tooling documentation.

## Quick Commands

```bash
# Tests
pytest --cov=app --cov-report=term-missing

# Lint & Format
ruff check app/ && ruff format app/

# Security scan (manual)
bandit -r app/ -ll
semgrep --config=auto app/

# Create PR
git push -u origin fix/issue-{num}-{desc}
"C:\Program Files\GitHub CLI\gh.exe" pr create \
  --title "fix(service): description" \
  --body "Closes #{num}" \
  --repo vscoder427/ProjectPhoenix
```

## Standards Level Quick Reference

| **Simple Fix** | **Moderate Change** | **Complex/Architectural** |
|----------------|---------------------|---------------------------|
| < 50 lines, 1 file | 2-5 files, new endpoint | Multiple services, breaking |
| Basic tests | Comprehensive tests | 85% coverage enforced |
| Lint passes | Update service docs | ADR required |
| Conventional commits | Update OpenAPI spec | Full release readiness |
| **Time: 30 min - 2 hrs** | **Time: 3-8 hrs** | **Time: 1-3 weeks** |

See [Service Development Workflow](service-development-workflow.md) for full details.
