# Service Development Workflow Guide

This guide explains how to fix bugs, add features, and refactor code in ProjectPhoenix microservices following disciplined practices while transitioning to full enterprise standards.

## Overview

**Purpose:** Standardize service development work (bug fixes, features, refactoring) across ProjectPhoenix microservices

**Audience:** Developers working on Dave, AAMeetings, CareerIntelligence, UserOnboarding, Outreach, ContentCreation, CareerTools, Marketing

**Complements:**
- [IaC GitHub Tracking Guide](iac-github-tracking.md) - For infrastructure/Terraform work
- [Standards Library](../standards/README.md) - Detailed standards for architecture, security, testing
- [Templates](../templates/README.md) - Decision records, service scaffolding checklists

**When to Use:** Fixing bugs, adding features, refactoring service code, updating dependencies

## Quick Start

```bash
# 1. Select issue and create branch
git checkout -b fix/issue-14-health-endpoint-500

# 2. Make changes, write tests
pytest --cov=app --cov-report=term-missing

# 3. Lint and format
ruff check app/ && ruff format app/

# 4. Commit with conventional format
git commit -m "fix(dave): handle missing config in health check"

# 5. Push and create PR
git push -u origin fix/issue-14-health-endpoint-500
"C:\Program Files\GitHub CLI\gh.exe" pr create \
  --title "fix(dave): handle missing config in health check" \
  --body "Closes #14" \
  --repo vscoder427/ProjectPhoenix
```

## Standards Levels: Minimal, Moderate, Full

ProjectPhoenix is transitioning from minimal standards (quick fixes) to full enterprise standards (comprehensive quality gates). Use this decision matrix to determine which level applies:

### Decision Matrix

| Scenario | Standards Level | Required Items |
|----------|----------------|----------------|
| **Simple bug fix** (< 50 lines, 1 file) | **Minimal** | Basic tests, conventional commits, lint passes |
| **Bug fix** (multi-file, < 200 lines) | **Minimal+** | Comprehensive tests, update service docs if behavior changes |
| **New endpoint/feature** | **Moderate** | Comprehensive tests, update OpenAPI spec, update service spec.md |
| **Architectural change** | **Full** | ADR, 85% coverage, release readiness checklist, security review |
| **HIPAA/security change** | **Full** | Security checklist, threat model review, ADR, compliance verification |
| **Breaking change** | **Full** | ADR, migration guide, semver MAJOR bump (1.0.0 → 2.0.0) |

### Standards Level Details

**Minimal Standards (Current Default):**
- ✅ Basic tests covering happy path + error case
- ✅ Conventional commits (`fix:`, `feat:`, `docs:`, `refactor:`, `test:`)
- ✅ Linting passes: `ruff check` and `ruff format`
- ✅ Update inline comments if logic changes
- ✅ Individual branch per issue: `fix/issue-{num}-{desc}`
- ❌ No formal ADR required
- ❌ No 85% coverage gate (but aim for good coverage)

**Moderate Standards:**
- ✅ All minimal standards
- ✅ Comprehensive tests (unit + integration)
- ✅ Update service spec.md if endpoints/behavior change
- ✅ Update runbook.md if operational procedures change
- ✅ Update OpenAPI spec if API changes
- ✅ Consider ADR if design choice is significant
- ✅ Update CHANGELOG.md
- ❌ 85% coverage target (not enforced yet)
- ❌ Full release readiness workflow (not enforced yet)

**Full Standards (Target State):**
- ✅ All moderate standards
- ✅ 85% test coverage achieved and enforced
- ✅ Formal ADR required for architectural decisions
- ✅ Full release readiness checklist generated
- ✅ Contract testing (Schemathesis) for API changes
- ✅ Security scan (Bandit, Trivy) passes
- ✅ Performance testing (k6) for user-facing changes
- ✅ SBOM generated and attached to release

## Workflow Phases

### Phase 1: Issue Selection & Understanding

**Goal:** Pick the right issue and understand what's needed

1. **Browse Issues:**
   - GitHub Issues: https://github.com/vscoder427/ProjectPhoenix/issues
   - Filter by label: `dave-service`, `bug`, `enhancement`, `critical`
   - Check milestone: Is this part of a larger phase?

2. **Assess Complexity:**
   - **Simple:** Single file, < 50 lines, obvious fix → Minimal standards
   - **Moderate:** 2-5 files, new endpoint, architectural impact → Moderate standards
   - **Complex:** Multiple services, breaking change, new patterns → Full standards

3. **Apply AI Development Guidelines:**
   - Review [AI-Native Development Standards](../standards/ai-native-development-standards.md) to determine tier:
     - **Green Tier:** AI autonomous (boilerplate code, test generation, documentation updates) → Proceed with standard verification
     - **Yellow Tier:** AI + human review (database changes, security code, API integrations) → Additional verification checkpoints required before merge
     - **Red Tier:** Human required (HIPAA compliance, production incidents, architecture decisions) → AI assists only, human leads
   - Use MCP servers following safety guidelines (see [MCP Safety](../standards/ai-native-development-standards.md#mcp-server-safety-guidelines))

4. **Check Dependencies:**
   - Look for "Blocked by: #X" in issue description
   - Check acceptance criteria - are they clear?
   - Verify you have local environment set up for the service

5. **Assign Yourself:**
   - Add yourself as assignee on GitHub
   - Add comment: "Working on this"

### Phase 2: Branch & Environment Setup

**Branch Naming Convention:**
- Bug fixes: `fix/issue-{number}-{short-description}`
- Features: `feat/issue-{number}-{short-description}`
- Docs: `docs/issue-{number}-{short-description}`
- Refactoring: `refactor/issue-{number}-{short-description}`

**Examples:**
```bash
git checkout -b fix/issue-14-production-rollout
git checkout -b feat/issue-11-vertex-ai-migration
git checkout -b refactor/issue-20-cleanup-auth-middleware
```

**Local Environment Setup:**

```bash
# Navigate to service directory
cd ProjectPhoenix/services/dave

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Test dependencies

# Set up local secrets (see service README.md)
# Copy .env.example to .env.local and fill in values

# Verify setup
pytest  # Should pass existing tests
uvicorn app.main:app --reload  # Should start service
```

### Phase 3: Implementation

**Development Loop:**

1. **Write a Failing Test First (TDD preferred):**
   ```python
   # tests/test_health.py
   def test_health_endpoint_handles_missing_config():
       """Health check should return 503 when config missing."""
       response = client.get("/health")
       assert response.status_code == 503
   ```

2. **Implement the Fix/Feature:**
   ```python
   # app/api/health.py
   @router.get("/health")
   async def health_check():
       if not config.is_loaded:
           raise HTTPException(status_code=503, detail="Config not loaded")
       return {"status": "healthy"}
   ```

3. **Run Tests:**
   ```bash
   pytest tests/test_health.py -v  # Run specific test
   pytest --cov=app --cov-report=term-missing  # Full suite with coverage
   ```

4. **Lint and Format:**
   ```bash
   ruff check app/  # Lint
   ruff format app/  # Auto-format
   ```

5. **Manual Testing:**
   ```bash
   uvicorn app.main:app --reload
   # Test in browser or with curl
   curl http://localhost:8000/health
   ```

**Code Quality Checklist:**
- [ ] Code follows [Coding Conventions](../standards/coding-conventions.md) (PEP 8, FastAPI patterns)
- [ ] Functions are < 50 lines (break up large functions)
- [ ] Type hints used (Pydantic models for request/response)
- [ ] No hardcoded secrets (use GCP Secret Manager)
- [ ] No PHI/PII in logs (use structured logging with redaction)
- [ ] Error handling uses FastAPI HTTPException
- [ ] Async patterns used correctly (async/await)

### Phase 4: Testing

**Testing Requirements by Standards Level:**

**Minimal Standards:**
```bash
# At minimum, test:
# - Happy path (success case)
# - Error case (most common failure)

# Example:
def test_get_user_success():
    response = client.get("/users/123")
    assert response.status_code == 200

def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
```

**Moderate Standards:**
```bash
# Comprehensive test coverage:
# - Unit tests for business logic
# - Integration tests for API endpoints
# - Edge cases and error conditions

pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage report
```

**Full Standards:**
```bash
# 85% coverage target + contract tests
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=85

# Contract testing (OpenAPI spec validation)
schemathesis run app/api/openapi.json --base-url http://localhost:8000

# Performance testing (if user-facing)
k6 run tests/load/baseline.js
```

**Reference:** [Testing and TDD Standard](../standards/testing-tdd.md)

### Phase 5: Documentation Updates

**Update docs based on what changed:**

| What Changed | Update These Docs |
|--------------|-------------------|
| Bug fix (logic only) | Inline code comments (if logic unclear) |
| API endpoint added/changed | `docs/services/{service}/spec.md`, OpenAPI spec |
| Operational procedure changed | `docs/services/{service}/runbook.md` |
| Architectural decision made | Create ADR in `docs/services/{service}/adr/` |
| Any production change | `CHANGELOG.md` |

**Example: Update Service Spec**

```bash
# Edit service spec to document new endpoint
code docs/services/dave/spec.md

# Add to API Contract section:
### GET /v1/career/goals
Returns user's career goals.

**Request:** None
**Response:** `CareerGoalsResponse` (see models)
**Auth:** JWT required
**Rate Limit:** 100 req/min
```

**When to Create an ADR:**
- Choosing between multiple architectural approaches
- Adopting a new technology or pattern
- Making a decision with long-term impact
- Security or compliance-related design choices

**ADR Template:** [ADR Standard](../standards/adr-standard.md)

**Quick Decision Record:** For smaller decisions, use [Decision Record (Lite)](../templates/decision-record-lite.md)

### Phase 6: Pull Request Creation

**PR Title Format (Conventional Commits):**

```
type(scope): brief summary

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- refactor: Code refactoring
- test: Test additions/updates
- chore: Build/tooling changes

Examples:
- fix(dave): handle missing config in health check
- feat(career-intel): add Redis caching for recommendations
- refactor(auth): extract JWT validation to middleware
- docs(dave): update runbook with Redis dependency
```

**Breaking Changes (use `!`):**
```
feat(dave)!: migrate from Gemini to Vertex AI

BREAKING CHANGE: All AI endpoints now use Vertex AI. Update client code to handle new response format.
```

**PR Body Template:**

```markdown
Closes #14

## Summary
[Brief description of what changed and why]

## Standards Level
- [ ] Minimal (simple fix, basic tests)
- [x] Moderate (comprehensive tests, docs updated)
- [ ] Full (ADR, 85% coverage, release readiness)

## Changes
- Fixed health endpoint 500 error by validating config on startup
- Added integration test for missing config scenario
- Updated service spec with error handling behavior

## Testing
- ✅ All existing tests pass
- ✅ New test added: `test_health_endpoint_handles_missing_config`
- ✅ Manual testing: verified 503 returned when config missing
- Coverage: 78% (up from 75%)

## Documentation Updated
- [x] Service spec.md updated (error handling section)
- [ ] Runbook.md (no operational changes)
- [ ] ADR created (not applicable)
- [x] CHANGELOG.md updated

## Checklist
- [x] Linting passed: `ruff check`
- [x] Formatting applied: `ruff format`
- [x] Tests written and passing
- [x] Conventional commit format used
- [x] Issue referenced: "Closes #14"
```

**Create PR with GitHub CLI:**

```bash
git push -u origin fix/issue-14-health-endpoint-500

"C:\Program Files\GitHub CLI\gh.exe" pr create \
  --title "fix(dave): handle missing config in health check" \
  --body-file pr-description.md \
  --repo vscoder427/ProjectPhoenix
```

**Assign Reviewers:**
- For minimal/moderate: One reviewer (peer developer)
- For full standards: Platform team + Security team (for security changes)

### Phase 7: Code Review & Merge

**Respond to Review Comments:**
- Address all comments or explain why not applicable
- Push additional commits (don't force push unless asked)
- Re-request review when ready

**Before Merging:**
- [ ] All CI checks pass
- [ ] Reviewers approved
- [ ] No merge conflicts
- [ ] Issue will auto-close (used "Closes #X" in PR body)

**Merge Strategy:**
- Use "Squash and merge" for clean history
- Final commit message will use PR title (ensure it's a good conventional commit)

### Phase 8: Post-Merge

**Verify Deployment:**
```bash
# Check if CI/CD deployed automatically
# Monitor Cloud Run logs
gcloud run services describe dave-service --region us-central1

# Or check GitHub Actions
"C:\Program Files\GitHub CLI\gh.exe" run list --repo vscoder427/ProjectPhoenix
```

**Cleanup:**
```bash
# Delete local branch
git checkout main
git pull
git branch -d fix/issue-14-health-endpoint-500

# Delete remote branch (usually auto-deleted by GitHub)
git push origin --delete fix/issue-14-health-endpoint-500
```

**Verify Issue Closed:**
- GitHub should auto-close issue via "Closes #14" in PR
- If not, manually close and reference PR: "Fixed in #PR-number"

## Transition Strategy

ProjectPhoenix is transitioning from minimal to full standards over time:

### Current State (Q1 2026) - Minimal Standards
✅ Conventional commits
✅ Basic tests for fixes
✅ Update docs when behavior changes
✅ Individual branches per issue
✅ Lint passes

### Intermediate State (Q2 2026 Target) - Moderate Standards
✅ All minimal standards
✅ 85% coverage for critical paths (auth, business logic, PHI handling)
✅ ADRs for all architectural changes
✅ Service specs kept current
✅ Contract testing for API changes

### Future State (Q3 2026 Target) - Full Standards
✅ All moderate standards
✅ 85% coverage enforced in CI
✅ Full release readiness workflow
✅ Automated security scanning in CI
✅ Performance testing before prod deploys
✅ SBOM generation

## Tools & Commands

### Essential Commands

```bash
# Testing
pytest                                    # Run all tests
pytest -v                                 # Verbose output
pytest --cov=app                          # With coverage
pytest --cov=app --cov-report=html        # HTML coverage report
pytest tests/test_health.py::test_func    # Run specific test

# Linting & Formatting
ruff check app/                           # Check for issues
ruff check app/ --fix                     # Auto-fix issues
ruff format app/                          # Format code
mypy app/                                 # Type checking (optional for minimal)

# Local Development
uvicorn app.main:app --reload             # Start dev server
uvicorn app.main:app --reload --port 8001 # Custom port

# Git
git checkout -b fix/issue-14-desc         # Create branch
git add app/ tests/                       # Stage changes
git commit -m "fix: description"          # Commit
git push -u origin fix/issue-14-desc      # Push first time
git push                                  # Subsequent pushes

# GitHub CLI
"C:\Program Files\GitHub CLI\gh.exe" pr create --title "..." --body "..."
"C:\Program Files\GitHub CLI\gh.exe" pr list --repo vscoder427/ProjectPhoenix
"C:\Program Files\GitHub CLI\gh.exe" issue list --label dave-service
```

### Useful Scripts

```bash
# Run full pre-commit checks
.\scripts\pre-commit-check.ps1            # If exists

# Generate coverage report
pytest --cov=app --cov-report=html
start htmlcov/index.html                  # Windows
```

## Reference Documentation

### Standards (Detailed Rules)
- [Testing and TDD](../standards/testing-tdd.md) - 85% coverage, pytest patterns
- [Coding Conventions](../standards/coding-conventions.md) - PEP 8, FastAPI patterns, error handling
- [Standards Governance](../standards/standards-governance.md) - Branch naming, conventional commits
- [CI/CD Deployment](../standards/ci-cd-deployment.md) - Semantic versioning, release process
- [Release Readiness](../standards/operations/release-readiness.md) - Full release checklist (for complex changes)

### Templates
- [ADR Standard](../standards/adr-standard.md) - When and how to create Architecture Decision Records
- [Decision Record (Lite)](../templates/decision-record-lite.md) - Quick decisions without full ADR
- [Service Spec Template](../standards/service-spec-template.md) - 10-section format for service documentation

### Guides
- [IaC GitHub Tracking](iac-github-tracking.md) - Workflow for infrastructure changes
- [Setup Versioning](setup-versioning.md) - Semantic versioning setup
- [Setup Terraform Backend](setup-terraform-backend.md) - IaC backend configuration

### Golden Service Reference
- **Location:** `services/golden-service-python/`
- **Use for:** Canonical FastAPI patterns, testing structure, CI/CD setup, dependency injection examples

When in doubt, check the Golden Service for the recommended implementation pattern.

## Examples

### Example 1: Simple Bug Fix (Minimal Standards)

**Issue:** "Fix 500 error in /health endpoint when config is missing"

**Estimated Complexity:** Simple (1 file, 15 lines)

**Workflow:**
```bash
# 1. Create branch
git checkout -b fix/issue-123-health-endpoint-500

# 2. Write test
# tests/test_health.py - add test_health_with_missing_config

# 3. Fix code
# app/api/health.py - add config validation

# 4. Run tests
pytest tests/test_health.py -v
pytest --cov=app/api/health.py

# 5. Lint
ruff check app/ && ruff format app/

# 6. Commit
git add app/ tests/
git commit -m "fix(dave): handle missing config in health check"

# 7. Push and create PR
git push -u origin fix/issue-123-health-endpoint-500
gh pr create --title "fix(dave): handle missing config in health check" \
  --body "Closes #123\n\nAdds config validation to health endpoint to prevent 500 errors."
```

**Docs Updated:** None (internal logic change only)

**Time:** ~30 minutes

### Example 2: Moderate Feature (Moderate Standards)

**Issue:** "Add caching layer to career recommendations endpoint"

**Estimated Complexity:** Moderate (3 files, Redis integration, 150 lines)

**Workflow:**
```bash
# 1. Create branch
git checkout -b feat/issue-124-career-rec-caching

# 2. Write tests (TDD)
# tests/test_career_recommendations.py
# - test_cache_hit_returns_cached_data
# - test_cache_miss_fetches_fresh_data
# - test_cache_expiration

# 3. Implement feature
# app/services/redis_client.py - Redis connection
# app/api/career.py - Add caching logic
# app/core/config.py - Add Redis config

# 4. Run comprehensive tests
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html - verify coverage increased

# 5. Update docs
# docs/services/dave/spec.md - Document caching behavior
# docs/services/dave/runbook.md - Add Redis dependency and troubleshooting
# CHANGELOG.md - Add entry

# 6. Lint
ruff check app/ && ruff format app/

# 7. Commit
git add app/ tests/ docs/
git commit -m "feat(dave): add Redis caching for career recommendations"

# 8. Create PR with detailed testing info
gh pr create --title "feat(dave): add Redis caching for career recommendations" \
  --body "Closes #124\n\n## Summary\nAdds Redis caching...\n\n## Testing\n[Include before/after latency metrics]"
```

**Docs Updated:** service spec.md, runbook.md, CHANGELOG.md

**Time:** ~3-4 hours

### Example 3: Complex Architectural Change (Full Standards)

**Issue:** "Migrate Dave from Gemini to Vertex AI for HIPAA compliance"

**Estimated Complexity:** Complex (15+ files, breaking change, security impact)

**Workflow:**
```bash
# 1. Create branch
git checkout -b feat/issue-11-vertex-ai-migration

# 2. Write ADR first
# docs/services/dave/adr/0003-vertex-ai-migration.md
# Document: Why Vertex AI, alternatives considered, security implications

# 3. Write comprehensive tests
# - Unit tests for Vertex AI client
# - Integration tests with Vertex AI
# - Contract tests for API endpoints
# - Load tests for performance
# Target: 85%+ coverage

# 4. Implement migration
# - Create new Vertex AI client
# - Update all AI endpoints
# - Update Pydantic models
# - Update error handling

# 5. Update all documentation
# docs/services/dave/spec.md - New AI endpoints
# docs/services/dave/runbook.md - Vertex AI ops procedures
# docs/services/dave/README.md - Updated setup instructions
# CHANGELOG.md - Breaking change documented

# 6. Security review
# - Complete HIPAA compliance checklist
# - Run Bandit, Trivy security scans
# - Verify BAA with GCP Vertex AI

# 7. Generate release artifacts
.\scripts\build-release-checklist.ps1

# 8. Commit (note the ! for breaking change)
git commit -m "feat(dave)!: migrate from Gemini to Vertex AI

BREAKING CHANGE: All AI endpoints now use Vertex AI.
Client code must be updated to handle new response format."

# 9. Create PR with full release readiness
gh pr create --title "feat(dave)!: migrate from Gemini to Vertex AI" \
  --body "Closes #11\n\n[Full release readiness checklist attached]"
```

**Docs Updated:** ADR, spec.md, runbook.md, README.md, CHANGELOG.md, release artifacts

**Time:** 2-3 weeks (multiple PRs recommended)

## Troubleshooting

### Tests Failing
```bash
# Run specific test with verbose output
pytest tests/test_health.py::test_func -vv

# Check test coverage to find untested code
pytest --cov=app --cov-report=term-missing

# Debug with breakpoint
# Add: import pdb; pdb.set_trace() in code
pytest tests/test_health.py -s
```

### Linting Errors
```bash
# See what's wrong
ruff check app/

# Auto-fix what's possible
ruff check app/ --fix

# Format code
ruff format app/

# If rules conflict with existing code, update pyproject.toml
```

### Import Errors in Tests
```bash
# Ensure you're in virtual environment
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install service in editable mode
pip install -e .
```

### Git Issues
```bash
# Merge conflict - rebase on main
git fetch origin
git rebase origin/main
# Resolve conflicts, then:
git rebase --continue

# Accidentally committed to main
git checkout -b fix/issue-123
git push -u origin fix/issue-123
```

## Getting Help

- **Standards Questions:** Check [Standards Library](../standards/README.md)
- **Service-Specific:** Check service README and runbook in `docs/services/{service}/`
- **Architecture Decisions:** Review ADRs in `docs/services/{service}/adr/`
- **Golden Service Reference:** `services/golden-service-python/`
- **GitHub Issues:** Ask questions in issue comments
- **Team:** Reach out to service owner (listed in service README.md)

## Next Steps

1. ✅ Read this guide
2. ✅ Pick an issue from backlog
3. ✅ Follow the workflow for your complexity level (minimal/moderate/full)
4. ✅ Reference [Quick Reference Checklist](dev-quick-reference.md) as you work
5. ✅ Ask questions in PR comments or issue threads

Happy coding!
