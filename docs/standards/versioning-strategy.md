# Versioning Strategy Standard

**Status:** Active
**Version:** 1.0
**Last Updated:** 2026-01-08
**Owner:** Engineering
**Applies To:** All ProjectPhoenix Services

## Purpose

This standard defines how ProjectPhoenix services manage versions, including version storage, automated bumping, API versioning, and deprecation policies. It ensures consistent, predictable version management across all microservices.

## Scope

Applies to:
- All ProjectPhoenix microservices (Dave, golden-service-python, future services)
- API endpoints exposed externally or internally
- Docker images and deployment artifacts
- Release documentation and changelogs

## Principles

1. **Independent Versioning:** Each service has its own semantic version
2. **Automation First:** Versions bump automatically based on commit messages
3. **Single Source of Truth:** One version file per service (`__version__.py`)
4. **API Versioning:** URL path-based versioning (`/api/v1/`, `/api/v2/`)
5. **Aggressive Deprecation:** 30-day deprecation windows for fast iteration

---

## 1. Semantic Versioning

### Version Format

All services use **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (incompatible API changes)
- **MINOR:** New features (backward-compatible functionality)
- **PATCH:** Bug fixes (backward-compatible fixes)

### Version Bumping Rules

Versions bump automatically based on conventional commit prefixes:

| Commit Type | Example | Bump |
|-------------|---------|------|
| `feat!:` or `BREAKING CHANGE:` | `feat!: require user_context field` | MAJOR (1.0.0 → 2.0.0) |
| `feat:` | `feat(chat): add history endpoint` | MINOR (1.0.0 → 1.1.0) |
| `fix:` | `fix(chat): correct JSON formatting` | PATCH (1.0.0 → 1.0.1) |
| `perf:` | `perf(db): optimize query performance` | PATCH |
| `refactor:` | `refactor(auth): simplify token validation` | PATCH |
| `docs:` | `docs: update API documentation` | No bump |
| `style:` | `style: fix code formatting` | No bump |
| `test:` | `test: add integration tests` | No bump |
| `chore:` | `chore: update dependencies` | No bump |

**Breaking Changes:**
- Must include `!` after type: `feat(scope)!: description`
- OR include `BREAKING CHANGE:` in commit body footer
- Always triggers MAJOR version bump

---

## 2. Version Storage

### Single Source of Truth

Each service stores its version in `__version__.py`:

**Location:** `services/<service-name>/api/app/__version__.py`

```python
"""
<Service Name> Version
Automatically updated by python-semantic-release
"""
__version__ = "1.2.3"
__version_tuple__ = (1, 2, 3)
```

### Version Synchronization

The version from `__version__.py` flows to:

1. **FastAPI OpenAPI Spec:** `app = FastAPI(version=__version__)`
2. **Health Endpoints:** `/metadata` response includes `"version": "1.2.3"`
3. **Git Tags:** Semantic-release creates `v1.2.3` tags
4. **Docker Images:** Tagged as `<service>:1.2.3`, `<service>:latest`
5. **CHANGELOG.md:** Auto-generated with version sections
6. **Release Artifacts:** `docs/releases/<service>/YYYY-MM-DD-v1.2.3/`
7. **Cloud Run:** Deployed with `APP_VERSION=1.2.3` env var

### Validation

CI enforces:
- `__version__.py` must exist for all services
- Version must follow SemVer format (`X.Y.Z`)
- Git tag must match version in `__version__.py`

---

## 3. Automated Version Management

### Tool: python-semantic-release

- **Version:** >= 9.0.0
- **Configuration:** Each service has `pyproject.toml` with `[tool.semantic_release]`
- **Trigger:** Push to `main` branch (via GitHub Actions)

### Configuration Template

`services/<service-name>/pyproject.toml`:

```toml
[tool.semantic_release]
version_variables = ["api/app/__version__.py:__version__"]
version_pattern = ["api/app/__version__.py:__version_tuple__ = \\({major}, {minor}, {patch}\\)"]
branch = "main"
upload_to_pypi = false
upload_to_release = true
build_command = false
commit_parser = "angular"
changelog_file = "CHANGELOG.md"

[tool.semantic_release.commit_parser_options]
major_tags = ["feat!"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf", "refactor", "docs", "style", "test", "chore"]
```

### Release Flow

1. **Merge to main** → GitHub Actions workflow triggered
2. **semantic-release version** → Updates `__version__.py` and `CHANGELOG.md`
3. **semantic-release publish** → Creates Git tag `vX.Y.Z` and GitHub release
4. **Docker build** → Builds and tags image with version
5. **Deploy** → Deploys versioned image to Cloud Run

---

## 4. API Versioning

### URL Path Versioning

All API endpoints use URL path versioning:

```
/api/v1/chat          ✅ Correct
/api/v2/chat          ✅ Correct
/chat                 ❌ Incorrect (no version)
```

### Router Structure

FastAPI services structure routes by version:

```python
# services/dave/api/app/routes/__init__.py

# V1 Router
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v1_router.include_router(chat_router, prefix="/chat")
v1_router.include_router(knowledge_router, prefix="/knowledge")

# V2 Router (when needed)
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
v2_router.include_router(chat_v2_router, prefix="/chat")

# Health endpoints (unversioned)
health_router = APIRouter()
health_router.include_router(health, tags=["health"])
```

### Version Compatibility Matrix

Each service maintains `docs/api-versions.md` documenting:
- Active versions
- Deprecated versions (with sunset dates)
- Sunset versions (no longer accessible)
- Breaking changes per version
- Migration guides

**Example:**

| Version | Status | Released | Sunset Date | Migration Guide |
|---------|--------|----------|-------------|-----------------|
| v2 | Active | 2026-02-01 | - | - |
| v1 | Deprecated | 2026-01-07 | 2026-03-07 | [v1 → v2 Guide](link) |

---

## 5. Deprecation Policy

### 30-Day Deprecation Window

**Policy:** All breaking changes follow a 30-day deprecation window.

**Process:**

1. **Day 0: Announce Deprecation**
   - Mark version as deprecated: `mark_deprecated("v1", sunset_days=30)`
   - Update `docs/api-versions.md` with sunset date
   - Publish migration guide

2. **Days 1-30: Warning Period**
   - All responses include RFC 8594 deprecation headers:
     ```
     Deprecation: true
     Sunset: Wed, 07 Feb 2026 00:00:00 GMT
     Link: <https://docs.employa.work/migration>; rel="deprecation"
     X-API-Deprecation-Days-Remaining: 15
     ```
   - Log all usage of deprecated endpoints
   - Monitor for heavy users

3. **Day 30: Sunset**
   - Deprecated endpoints return `410 Gone`
   - Response body: `{"error": "API version v1 has been sunset"}`

4. **Post-Sunset: Code Removal**
   - Remove deprecated router and route files
   - Update `docs/api-versions.md` to move version to "Sunset" section
   - Create follow-up PR to delete deprecated code

### Deprecation Middleware

All services include deprecation middleware that:
- Detects API version from request path (`/api/v1/*`)
- Checks deprecation status against `DEPRECATION_REGISTRY`
- Adds headers for deprecated versions
- Blocks requests to sunset versions (returns 410)
- Logs deprecated endpoint usage with client info

---

## 6. Release Artifacts

### Git Tags

- **Format:** `v{MAJOR}.{MINOR}.{PATCH}` (e.g., `v1.2.3`)
- **Created by:** python-semantic-release
- **Annotated:** Yes (includes release notes)

### Docker Images

- **Registry:** GCR (`gcr.io/PROJECT_ID/<service>`)
- **Tags:**
  - `<service>:<version>` (e.g., `dave-service:1.2.3`) - Immutable
  - `<service>:latest` - Mutable, points to latest version
  - `<service>:<build-id>` - Build-specific tag

### CHANGELOG.md

- **Location:** `services/<service>/CHANGELOG.md`
- **Format:** Keep a Changelog (https://keepachangelog.com/)
- **Auto-generated:** By python-semantic-release
- **Sections:** Added, Changed, Deprecated, Removed, Fixed, Security

### Release Directory

Each release creates a directory:

`docs/releases/<service>/{YYYY-MM-DD}-v{version}/`

Contains:
- `readiness.md` - Release readiness checklist
- `notes.md` - Release notes
- `sbom.html` - Software Bill of Materials
- `security-scans.md` - Security scan results
- `config.md` - Configuration changes

---

## 7. Testing Requirements

### Version Tests

Each service must include:

**Unit Tests** (`tests/test_versioning.py`):
- Version exposed in `/metadata` endpoint
- Deprecation registry functions correctly
- Deprecated endpoints include headers
- Sunset endpoints return 410
- Active endpoints have no deprecation headers

**Integration Tests** (`tests/integration/test_version_flow.py`):
- `__version__.py` exists and is importable
- `pyproject.toml` has semantic-release config
- Version extractable during Docker build

### CI Checks

Pre-merge guardrails enforce:
- `__version__.py` exists for all services
- No sunset API versions in codebase (`scripts/check-sunset-versions.py`)
- Conventional commit messages validated
- All version tests pass

---

## 8. Developer Workflow

### Making Changes

```bash
# 1. Create branch
git checkout -b fix/chat-formatting

# 2. Make changes, commit with conventional commit
git commit -m "fix(chat): correct JSON formatting in responses"

# 3. Push and create PR
git push origin fix/chat-formatting
gh pr create --title "fix(chat): correct JSON formatting"

# 4. Merge to main (after review and CI passes)
gh pr merge --auto --squash

# 5. Semantic release runs automatically
# - Detects "fix:" → PATCH bump
# - 1.2.3 → 1.2.4
# - Creates tag, updates CHANGELOG, deploys
```

### Preview Version Bump

Use pre-commit hook (optional):

```bash
# Install hook
./scripts/install-hooks.sh

# After staging commits, shows:
# 📦 Current version: 1.2.3
# 🚀 Next version (PATCH): 1.2.4
```

### Manual Release (Rare)

```bash
# Use helper script
./scripts/release.sh dave

# Or trigger workflow manually
gh workflow run semantic-release.yml -f service=dave -f dry_run=false
```

### Rollback

```bash
# Rollback to previous version
./scripts/rollback.sh dave 1.2.3

# Verifies tag exists, then redeploys that version to Cloud Run
```

---

## 9. Breaking Changes

### Guidelines

**What qualifies as a breaking change:**
- Removing or renaming endpoints
- Changing request/response schemas
- Changing authentication requirements
- Changing behavior that clients depend on
- Removing query parameters or headers

**What is NOT a breaking change:**
- Adding new optional fields
- Adding new endpoints
- Improving error messages
- Performance improvements
- Internal refactoring

### Introducing Breaking Changes

1. **Develop new version** (e.g., v2) alongside existing version
2. **Mark old version deprecated** when releasing v2
3. **Provide migration guide** documenting all changes
4. **30-day warning period** before sunset
5. **Remove old code** after sunset

**Example commit:**

```bash
git commit -m "feat(chat)!: require user_context in chat requests

BREAKING CHANGE: Chat endpoint now requires user_context field
in request body for improved personalization.

Migration: Add user_context object with user_id and session_id
to all chat API requests. See migration guide at:
https://docs.employa.work/api/v2/migration-from-v1"
```

---

## 10. Compliance and Audit

### Version History

All version changes tracked via:
- Git tags (immutable history)
- CHANGELOG.md (human-readable)
- GitHub Releases (with release notes)
- Release artifact directories (`docs/releases/`)

### Release Readiness

Each release requires completed checklist including:
- Version validation (bumped correctly)
- CHANGELOG updated
- API compatibility matrix current
- Deprecation status reviewed
- Security scans clean
- All tests passing

### Deprecation Tracking

Supabase table (optional) tracks:
- Which versions are deprecated
- Sunset dates
- Usage metrics for deprecated endpoints
- Affected clients

---

## 11. Exceptions

### Services Exempt from Versioning

None. All ProjectPhoenix services must follow this standard.

### Special Cases

- **Internal-only services:** Still use semantic versioning but may skip API versioning (no `/api/v1/` prefix)
- **Experimental features:** Can use `/api/experimental/` prefix, no deprecation policy applies

---

## 12. Related Standards

- [API Lifecycle Governance](./api-lifecycle-governance.md) - API lifecycle management
- [CI/CD and Deployment](./ci-cd-deployment.md) - Release automation
- [API Conventions](./api-conventions.md) - API design standards
- [Changelog Format](./changelog-format.md) - Changelog structure

---

## 13. References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [RFC 8594: Sunset HTTP Header](https://datatracker.ietf.org/doc/html/rfc8594)
- [python-semantic-release Documentation](https://python-semantic-release.readthedocs.io/)
- [Keep a Changelog](https://keepachangelog.com/)

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-08 | Initial versioning strategy standard | Engineering |
