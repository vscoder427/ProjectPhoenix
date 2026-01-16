# CI/CD and Deployment Standard

This standard defines CI/CD pipelines, environments, and deployment practices for all Employa microservices.

## Version Management

- Semantic versioning enforced via python-semantic-release
- Version automatically bumped on merge to main based on commit messages:
  - `feat!:` or `BREAKING CHANGE:` → MAJOR bump (1.0.0 → 2.0.0)
  - `feat:` → MINOR bump (1.0.0 → 1.1.0)
  - `fix:`, `perf:`, `refactor:` → PATCH bump (1.0.0 → 1.0.1)
- Single source of truth in `api/app/__version__.py`

## Release Process

6-step automated flow:

1. **Merge** to main (triggers semantic-release workflow)
2. **Bump** version in `__version__.py` and `CHANGELOG.md`
3. **Tag** Git repository with `vX.Y.Z`
4. **Release** Create GitHub release with notes
5. **Build** Docker image tagged with version
6. **Deploy** Versioned image to Cloud Run

## CI Workflow

### Required Jobs

| Job | Tools | Failure Policy |
|-----|-------|----------------|
| **Lint & Type Check** | Ruff, Pyright (Python) / ESLint (JS) | Block merge |
| **Unit Tests** | pytest / Jest | Block merge |
| **SAST** | Bandit, Semgrep | Block on HIGH |
| **SCA** | pip-audit / npm audit | Block on CRITICAL |
| **Container Scan** | Trivy | Block on CRITICAL unfixed |
| **Build Validation** | Docker build | Block merge |

### Security Scanning Requirements

All services MUST include security scanning in CI:

```yaml
# Python services
security-scan:
  steps:
    - run: bandit -r app/ -ll
    - run: semgrep --config=auto app/
    - run: pip-audit --strict

# Container scanning (any service with Dockerfile)
container-security:
  steps:
    - uses: aquasecurity/trivy-action@0.28.0
      with:
        image-ref: '${{ service }}:scan'
        severity: 'CRITICAL,HIGH'
        exit-code: '1'
        ignore-unfixed: true
```

See [security/security-scanning.md](security/security-scanning.md) for complete configuration.

### CI Checks

- Lint + tests + security scans (SAST/SCA)
- Container scanning (Trivy) required for Dockerized services
- Version file validation (check `__version__.py` exists)
- Sunset version check (no expired API versions)
- All checks required before merge

## Deployment Triggers

- Auto-deploy to dev and staging on merge to `main`
- Manual approval required for prod deploys

## Environments

- Dev, Staging, and Prod environments required
- Shared image promotion pipeline across environments

## Rollout Strategy

- Progressive canary rollouts with automatic rollback on SLO breach

## Artifact Naming

- **Docker images:** `service:X.Y.Z`, `service:latest`, `service:$BUILD_ID`
- **Git tags:** `vX.Y.Z`
- **Release directories:** `docs/releases/service/YYYY-MM-DD-vX.Y.Z/`

## Release Management

- Release notes required for every production deploy
- Post-deploy verification checklist required

See [Versioning Strategy](./versioning-strategy.md) for complete version management details.
