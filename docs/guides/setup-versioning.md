# Versioning Setup Guide

This guide provides step-by-step instructions for implementing the ProjectPhoenix versioning strategy. Follow these instructions to set up automated versioning for a service.

**Target Services:** Dave, golden-service-python (and future services)
**Estimated Time:** 4 weeks (1-2 hours/day)
**Prerequisites:** Git, Python 3.12, GitHub CLI (`gh`)

---

## Table of Contents

1. [Week 1: Foundation](#week-1-foundation)
2. [Week 2: Automation](#week-2-automation)
3. [Week 3: Standards & Testing](#week-3-standards--testing)
4. [Week 4: Helper Tools](#week-4-helper-tools)
5. [Troubleshooting](#troubleshooting)

---

## Week 1: Foundation

### Day 1: Version Storage Module

**Goal:** Create `__version__.py` as single source of truth

#### Step 1.1: Create Version File (Dave Service)

```bash
cd services/dave/api/app

# Create __version__.py
cat > __version__.py << 'EOF'
"""
Dave Service Version
Automatically updated by python-semantic-release
"""
__version__ = "0.1.0"
__version_tuple__ = (0, 1, 0)
EOF
```

**Validation:**
```bash
python -c "import sys; sys.path.insert(0, 'services/dave/api'); from app import __version__; print(__version__.__version__)"
# Expected output: 0.1.0
```

#### Step 1.2: Update __init__.py (Dave Service)

```bash
cd services/dave/api/app
```

Edit `__init__.py` to add:

```python
from .__version__ import __version__, __version_tuple__

__all__ = ["__version__", "__version_tuple__"]
```

**Validation:**
```bash
python -c "import sys; sys.path.insert(0, 'services/dave/api'); from app import __version__; print(__version__)"
# Expected output: 0.1.0
```

#### Step 1.3: Update main.py (Dave Service)

Edit `services/dave/api/app/main.py`:

**Find:**
```python
app = FastAPI(
    title=settings.service_name,
    version="0.1.0",  # Hardcoded version
    ...
)
```

**Replace with:**
```python
from app import __version__

app = FastAPI(
    title=settings.service_name,
    version=__version__,  # Dynamic version
    ...
)
```

**Validation:**
```bash
cd services/dave/api
uvicorn app.main:app --reload &
sleep 3
curl http://localhost:8000/docs | grep -o '"version":"[^"]*"'
# Expected output: "version":"0.1.0"
pkill -f uvicorn
```

#### Step 1.4: Update config.py (Dave Service)

Edit `services/dave/api/app/config.py` to add version property:

```python
from app import __version__

class Settings(BaseSettings):
    # ... existing fields ...

    @property
    def app_version(self) -> str:
        """Get application version."""
        return __version__
```

**Validation:**
```bash
python -c "import sys; sys.path.insert(0, 'services/dave/api'); from app.config import settings; print(settings.app_version)"
# Expected output: 0.1.0
```

#### Step 1.5: Repeat for golden-service-python

Repeat steps 1.1-1.4 for `services/golden-service-python/`.

---

### Day 2: Semantic Release Configuration

**Goal:** Set up python-semantic-release for automated version bumping

#### Step 2.1: Add Dependency (Dave Service)

```bash
cd services/dave

# Add to requirements.in
echo "python-semantic-release>=9.0.0" >> requirements.in

# Compile requirements.txt
pip-compile requirements.in
```

**Validation:**
```bash
grep "python-semantic-release" requirements.txt
# Should show python-semantic-release>=9.0.0
```

#### Step 2.2: Create pyproject.toml (Dave Service)

```bash
cd services/dave

cat > pyproject.toml << 'EOF'
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

[tool.semantic_release.changelog]
template_dir = "../../scripts/release-templates"
exclude_commit_patterns = []

[tool.semantic_release.remote]
type = "github"
token = { env = "GITHUB_TOKEN" }
EOF
```

**Validation:**
```bash
# Install semantic-release
pip install python-semantic-release

# Test dry-run (no changes)
semantic-release version --no-commit --no-tag --no-push
# Should show current version and next version prediction
```

#### Step 2.3: Initialize CHANGELOG.md (Dave Service)

```bash
cd services/dave

cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to Dave Service will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## 0.1.0 - 2026-01-07

### Added
- Initial Dave service implementation
- Chat API with streaming support
- Knowledge base search
- Prompt management
EOF
```

#### Step 2.4: Repeat for golden-service-python

Repeat steps 2.1-2.3 for `services/golden-service-python/`.

---

### Day 3: API Versioning Structure

**Goal:** Create version management and deprecation middleware

#### Step 3.1: Create versions.py (Dave Service)

```bash
cd services/dave/api/app

# Create routes directory if it doesn't exist
mkdir -p routes

# Use template
cp ../../../../docs/templates/version-module-template.py routes/versions.py
```

Or create manually:

```bash
cat > routes/versions.py << 'EOF'
"""
API Version Management
Handles version routing and deprecation tracking
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    # V2 = "v2"  # Add when needed


class DeprecationStatus(BaseModel):
    """Deprecation status for an API version."""
    version: str
    deprecated: bool
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None
    days_until_sunset: Optional[int] = None


# Deprecation registry
DEPRECATION_REGISTRY: dict[str, DeprecationStatus] = {
    "v1": DeprecationStatus(
        version="v1",
        deprecated=False,
        sunset_date=None,
        migration_guide=None,
    ),
}


def mark_deprecated(
    version: str,
    sunset_days: int = 30,
    migration_guide: str | None = None,
) -> None:
    """Mark an API version as deprecated."""
    sunset_date = datetime.utcnow() + timedelta(days=sunset_days)
    DEPRECATION_REGISTRY[version] = DeprecationStatus(
        version=version,
        deprecated=True,
        sunset_date=sunset_date,
        days_until_sunset=sunset_days,
        migration_guide=migration_guide or f"https://docs.employa.work/api/{version}/migration",
    )


def get_deprecation_status(version: str) -> DeprecationStatus | None:
    """Get deprecation status for a version."""
    return DEPRECATION_REGISTRY.get(version)


def is_deprecated(version: str) -> bool:
    """Check if a version is deprecated."""
    status = DEPRECATION_REGISTRY.get(version)
    return status.deprecated if status else False


def is_sunset(version: str) -> bool:
    """Check if a version has passed its sunset date."""
    status = DEPRECATION_REGISTRY.get(version)
    if not status or not status.sunset_date:
        return False
    return datetime.utcnow() > status.sunset_date
EOF
```

**Validation:**
```bash
python -c "import sys; sys.path.insert(0, 'services/dave/api'); from app.routes.versions import APIVersion; print(APIVersion.V1)"
# Expected output: v1
```

#### Step 3.2: Create deprecation middleware (Dave Service)

```bash
cd services/dave/api/app

mkdir -p middleware

# Use template
cp ../../../../docs/templates/deprecation-middleware-template.py middleware/deprecation.py
```

Or create manually (see template file for full code).

#### Step 3.3: Refactor routers for /api/v1/ prefix

Edit `services/dave/api/app/routes/__init__.py`:

```python
"""
API Router Setup with Versioning
"""
from fastapi import APIRouter

from app.routes.versions import APIVersion
from .chat import router as chat_router
from .health import router as health_router
from .knowledge import router as knowledge_router
from .prompts import router as prompts_router

# Health checks (root level - no versioning)
health = APIRouter()
health.include_router(health_router, tags=["health"])

# API V1 Routes
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v1_router.include_router(chat_router, prefix="/chat", tags=["chat"])
v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
v1_router.include_router(prompts_router, prefix="/admin/prompts", tags=["admin"])

# Main router
router = APIRouter()
router.include_router(health)
router.include_router(v1_router)
```

Update `services/dave/api/app/main.py`:

```python
# Add deprecation middleware
from app.middleware.deprecation import DeprecationMiddleware

# After existing middleware
app.add_middleware(DeprecationMiddleware)

# Include routers (simplified)
from app.routes import router
app.include_router(router)
```

**Validation:**
```bash
cd services/dave/api
uvicorn app.main:app --reload &
sleep 3

# Test v1 endpoint
curl http://localhost:8000/api/v1/health
# Should return health status

# Test health endpoint (unversioned)
curl http://localhost:8000/health
# Should return health status

pkill -f uvicorn
```

#### Step 3.4: Create API version documentation

```bash
cd services/dave/docs

cat > api-versions.md << 'EOF'
# API Version Compatibility Matrix

## Active Versions

| Version | Status | Released | Sunset Date | Breaking Changes | Migration Guide |
|---------|--------|----------|-------------|------------------|-----------------|
| v1      | Active | 2026-01-07 | - | N/A | - |

## Deprecated Versions

None

## Sunset Versions

None

## Version Support Policy

- **Active:** Full support, recommended for all new integrations
- **Deprecated:** 30-day warning period, still functional but sunset date announced
- **Sunset:** No longer accessible, returns 410 Gone

## Breaking Changes by Version

### v1 (Current)
- Initial release
- All endpoints under `/api/v1/*`
EOF
```

#### Step 3.5: Repeat for golden-service-python

Repeat steps 3.1-3.4 for `services/golden-service-python/`.

---

## Week 2: Automation

### Day 1: GitHub Actions Workflow

**Goal:** Automate version bumping on merge to main

#### Step 4.1: Create semantic-release workflow

```bash
cd .github/workflows

cat > semantic-release.yml << 'EOF'
name: Semantic Release

on:
  push:
    branches:
      - main
    paths:
      - 'services/dave/**'
      - 'services/golden-service-python/**'
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to release (dave, golden-service-python, or all)'
        required: true
        default: 'all'
        type: choice
        options:
          - dave
          - golden-service-python
          - all
      dry_run:
        description: 'Dry run (no actual release)'
        required: false
        default: false
        type: boolean

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      dave_changed: ${{ steps.changes.outputs.dave }}
      golden_changed: ${{ steps.changes.outputs.golden }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            dave:
              - 'services/dave/**'
            golden:
              - 'services/golden-service-python/**'

  release-dave:
    needs: detect-changes
    if: |
      (needs.detect-changes.outputs.dave_changed == 'true' && github.event_name == 'push') ||
      (github.event_name == 'workflow_dispatch' && (inputs.service == 'dave' || inputs.service == 'all'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: services/dave
        run: |
          pip install python-semantic-release

      - name: Run semantic-release (dry run)
        if: inputs.dry_run
        working-directory: services/dave
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          semantic-release version --no-commit --no-tag --no-push
          semantic-release changelog

      - name: Run semantic-release
        if: ${{ !inputs.dry_run }}
        working-directory: services/dave
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          semantic-release version
          semantic-release publish

      - name: Get new version
        id: version
        working-directory: services/dave
        run: |
          VERSION=$(python -c "import sys; sys.path.insert(0, 'api'); from app import __version__; print(__version__)")
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Released Dave v$VERSION"

  release-golden:
    needs: detect-changes
    if: |
      (needs.detect-changes.outputs.golden_changed == 'true' && github.event_name == 'push') ||
      (github.event_name == 'workflow_dispatch' && (inputs.service == 'golden-service-python' || inputs.service == 'all'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: services/golden-service-python
        run: |
          pip install python-semantic-release

      - name: Run semantic-release
        if: ${{ !inputs.dry_run }}
        working-directory: services/golden-service-python
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          semantic-release version
          semantic-release publish

      - name: Get new version
        id: version
        working-directory: services/golden-service-python
        run: |
          VERSION=$(python -c "import sys; sys.path.insert(0, 'api'); from app import __version__; print(__version__)")
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Released golden-service v$VERSION"
EOF
```

**Validation:**
```bash
# Test workflow syntax
"C:\Program Files\GitHub CLI\gh.exe" workflow list
# Should show semantic-release in the list

# Manual test (dry run)
"C:\Program Files\GitHub CLI\gh.exe" workflow run semantic-release.yml -f service=dave -f dry_run=true
```

---

### Day 2: Docker Build Integration

**Goal:** Tag Docker images with semantic version

#### Step 5.1: Update cloudbuild.yaml (Dave Service)

Edit `services/dave/cloudbuild.yaml`:

**Add version extraction step:**
```yaml
steps:
  # Extract version from __version__.py
  - name: 'python:3.12-slim'
    entrypoint: 'python'
    args:
      - '-c'
      - |
        import sys
        sys.path.insert(0, 'services/dave/api')
        from app import __version__
        with open('/workspace/_version.txt', 'w') as f:
            f.write(__version__)
    id: 'extract-version'
```

**Update build step:**
```yaml
  # Build with version tag
  - name: 'gcr.io/cloud-builders/docker'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        VERSION=$(cat /workspace/_version.txt)
        docker build \
          -t gcr.io/$PROJECT_ID/dave-service:$BUILD_ID \
          -t gcr.io/$PROJECT_ID/dave-service:$VERSION \
          -t gcr.io/$PROJECT_ID/dave-service:latest \
          -f services/dave/Dockerfile \
          --build-arg VERSION=$VERSION \
          .
```

**Update push step:**
```yaml
  # Push all tags
  - name: 'gcr.io/cloud-builders/docker'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        VERSION=$(cat /workspace/_version.txt)
        docker push gcr.io/$PROJECT_ID/dave-service:$BUILD_ID
        docker push gcr.io/$PROJECT_ID/dave-service:$VERSION
        docker push gcr.io/$PROJECT_ID/dave-service:latest
```

**Update deploy step:**
```yaml
  # Deploy with version
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        VERSION=$(cat /workspace/_version.txt)
        gcloud run deploy dave-service \
          --image=gcr.io/$PROJECT_ID/dave-service:$VERSION \
          --region=us-central1 \
          --platform=managed \
          --set-env-vars=APP_VERSION=$VERSION \
          # ... rest of deploy config
```

**Validation:** (Will test during actual deployment)

#### Step 5.2: Repeat for golden-service-python

Apply same changes to `services/golden-service-python/cloudbuild.yaml`.

---

### Day 3: Update Pre-Merge Guardrails

**Goal:** Add version validation to CI

#### Step 6.1: Update pre-merge-guardrails.yml

Edit `.github/workflows/pre-merge-guardrails.yml`:

**Add version file check:**
```yaml
      - name: Validate version files exist
        run: |
          python - <<'PY'
          import sys
          from pathlib import Path

          services = ["dave", "golden-service-python"]
          missing = []

          for service in services:
              version_file = Path(f"services/{service}/api/app/__version__.py")
              if not version_file.exists():
                  missing.append(f"{service}: {version_file}")

          if missing:
              print("❌ Missing __version__.py files:")
              for m in missing:
                  print(f"  - {m}")
              sys.exit(1)

          print("✅ All services have __version__.py")
          PY
```

**Validation:**
```bash
# Run check locally
python - <<'PY'
import sys
from pathlib import Path

services = ["dave", "golden-service-python"]
missing = []

for service in services:
    version_file = Path(f"services/{service}/api/app/__version__.py")
    if not version_file.exists():
        missing.append(f"{service}: {version_file}")

if missing:
    print("❌ Missing __version__.py files:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)

print("✅ All services have __version__.py")
PY
```

---

## Week 3: Standards & Testing

### Day 1: Update Standards Documentation

**Goal:** Update existing standards to reference versioning

#### Step 7.1: Update api-lifecycle-governance.md

Add to [docs/standards/api-lifecycle-governance.md](../standards/api-lifecycle-governance.md):

```markdown
## Version Management

- Services use Semantic Versioning (MAJOR.MINOR.PATCH)
- Version stored in `api/app/__version__.py`
- Breaking changes increment MAJOR version
- New features increment MINOR version
- Bug fixes increment PATCH version

## Deprecation Window

- **Policy:** 30-day deprecation window for breaking changes
- **Process:**
  1. Mark version deprecated via `mark_deprecated()` function
  2. Add RFC 8594 headers to all responses
  3. Log usage of deprecated endpoints
  4. After 30 days, return 410 Gone
  5. Remove deprecated code after sunset

See [Versioning Strategy](./versioning-strategy.md) for details.
```

#### Step 7.2: Update ci-cd-deployment.md

Add to [docs/standards/ci-cd-deployment.md](../standards/ci-cd-deployment.md):

```markdown
## Version Management

- python-semantic-release automatically bumps versions on merge to main
- Version bump rules:
  - `feat!:` or `BREAKING CHANGE:` → MAJOR
  - `feat:` → MINOR
  - `fix:`, `perf:`, `refactor:` → PATCH
- Git tags created automatically: `vX.Y.Z`
- Docker images tagged with version: `service:X.Y.Z`

See [Versioning Strategy](./versioning-strategy.md) for details.
```

#### Step 7.3: Update api-conventions.md

Add to [docs/standards/api-conventions.md](../standards/api-conventions.md):

```markdown
## API Versioning

- **URL Path Versioning:** All endpoints under `/api/v1/`, `/api/v2/`, etc.
- **Deprecation Headers:** RFC 8594 `Deprecation` and `Sunset` headers
- **Version Compatibility Matrix:** Maintained in `docs/api-versions.md`
- **30-Day Deprecation Window:** All breaking changes follow 30-day notice

See [Versioning Strategy](./versioning-strategy.md) for details.
```

---

### Day 2: Create Tests

**Goal:** Write version-related tests

#### Step 8.1: Create test_versioning.py (Dave Service)

```bash
cd services/dave

mkdir -p tests
cat > tests/test_versioning.py << 'EOF'
"""Tests for versioning and deprecation system."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.versions import (
    mark_deprecated,
    get_deprecation_status,
    is_deprecated,
    is_sunset,
    DEPRECATION_REGISTRY,
)

client = TestClient(app)


def test_version_in_metadata():
    """Version should be exposed in /metadata endpoint."""
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["version"].count(".") == 2  # Semantic version


def test_mark_deprecated():
    """Should mark version as deprecated with sunset date."""
    mark_deprecated("v1-test", sunset_days=30, migration_guide="http://example.com/guide")

    status = get_deprecation_status("v1-test")
    assert status is not None
    assert status.deprecated is True
    assert status.days_until_sunset == 30
    assert status.migration_guide == "http://example.com/guide"

    # Clean up
    del DEPRECATION_REGISTRY["v1-test"]


def test_deprecation_headers():
    """Deprecated endpoints should include deprecation headers."""
    # Mark v1 as deprecated
    mark_deprecated("v1", sunset_days=15)

    response = client.get("/api/v1/health")

    assert "Deprecation" in response.headers
    assert response.headers["Deprecation"] == "true"

    # Clean up
    DEPRECATION_REGISTRY["v1"].deprecated = False


def test_non_deprecated_no_headers():
    """Active versions should not have deprecation headers."""
    response = client.get("/api/v1/health")

    assert "Deprecation" not in response.headers
    assert "Sunset" not in response.headers
EOF
```

**Validation:**
```bash
cd services/dave
pytest tests/test_versioning.py -v
# Should pass all tests
```

#### Step 8.2: Repeat for golden-service-python

---

### Day 3: Update Release Checklist Builder

**Goal:** Include version info in release checklists

#### Step 9.1: Update build-release-checklist.ps1

Edit `scripts/build-release-checklist.ps1` to extract and include version:

```powershell
# Extract version from tag (v1.2.3 → 1.2.3)
$Version = $ReleaseTag -replace '^v', ''

# Read version info from service
$VersionFile = "services/$ServiceName/api/app/__version__.py"
$CurrentVersion = "unknown"
if (Test-Path $VersionFile) {
    $Content = Get-Content $VersionFile
    $VersionLine = $Content | Where-Object { $_ -match '__version__\s*=\s*"([^"]+)"' }
    if ($Matches) {
        $CurrentVersion = $Matches[1]
    }
}

# Add to checklist content
$content = @"
## Version Information
- [ ] Version bumped correctly: $CurrentVersion
- [ ] CHANGELOG.md updated
- [ ] Git tag created: $ReleaseTag
- [ ] API compatibility matrix updated
"@
```

---

## Week 4: Helper Tools

### Day 1: Release Helper Script

**Goal:** Create CLI tool for releases

#### Step 10.1: Create scripts/release.sh

See full script in [plan file](../../.claude/plans/replicated-greeting-feigenbaum.md#71-pre-commit-hook-for-version-preview).

```bash
chmod +x scripts/release.sh

# Test dry-run
./scripts/release.sh dave dry-run
```

---

### Day 2: Rollback Script

**Goal:** Create rollback tool

#### Step 11.1: Create scripts/rollback.sh

See full script in plan file.

```bash
chmod +x scripts/rollback.sh
```

---

### Day 3: Pre-Commit Hook

**Goal:** Preview version bumps before committing

#### Step 12.1: Create scripts/git-hooks/pre-commit-version-check

See full script in plan file.

#### Step 12.2: Create scripts/install-hooks.sh

```bash
cat > scripts/install-hooks.sh << 'EOF'
#!/bin/bash
# Install git hooks

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."

# Pre-commit hook
cp "$REPO_ROOT/scripts/git-hooks/pre-commit-version-check" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Hooks installed successfully"
EOF

chmod +x scripts/install-hooks.sh

# Install hooks
./scripts/install-hooks.sh
```

---

## Troubleshooting

### semantic-release not bumping version

**Symptom:** Version stays at 0.1.0 after merge

**Causes:**
1. Commit message doesn't follow conventional commits
2. `pyproject.toml` misconfigured
3. No commits since last tag that warrant bump

**Fix:**
```bash
# Check commit messages
git log --oneline -5

# Verify pyproject.toml exists
ls services/dave/pyproject.toml

# Test manually
cd services/dave
semantic-release version --no-commit --no-tag --no-push -vv
```

---

### Docker build can't find version

**Symptom:** Build fails with "ModuleNotFoundError: No module named 'app'"

**Fix:**
```bash
# Verify __version__.py exists
ls services/dave/api/app/__version__.py

# Check Python path in cloudbuild.yaml
# Should be: sys.path.insert(0, 'services/dave/api')
```

---

### Deprecation headers not appearing

**Symptom:** Deprecated endpoints don't show headers

**Fix:**
```bash
# Verify middleware is registered
grep "DeprecationMiddleware" services/dave/api/app/main.py

# Check deprecation status
python -c "import sys; sys.path.insert(0, 'services/dave/api'); from app.routes.versions import DEPRECATION_REGISTRY; print(DEPRECATION_REGISTRY)"
```

---

### CI failing on version check

**Symptom:** Pre-merge guardrails fail with "Missing __version__.py"

**Fix:**
```bash
# Verify files exist
ls services/dave/api/app/__version__.py
ls services/golden-service-python/api/app/__version__.py

# If missing, create them (see Day 1)
```

---

## Next Steps

After completing all 4 weeks:

1. **Test end-to-end:** Make a commit, merge to main, verify version bumps
2. **Document:** Update team wiki with versioning workflow
3. **Monitor:** Watch first few automated releases closely
4. **Iterate:** Adjust deprecation windows if needed

**Questions?** Reference [docs/standards/versioning-strategy.md](../standards/versioning-strategy.md) or create a GitHub issue.
