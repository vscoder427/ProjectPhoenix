# Security Scanning Standard

**Status:** Active
**Last Updated:** 2026-01-15
**Applies To:** All Employa services

## Overview

All Employa services must implement layered security scanning to meet HIPAA compliance requirements. This standard defines the required tools, configurations, and integration patterns.

## Required Security Layers

| Layer | Tool | When | Failure Policy |
|-------|------|------|----------------|
| **SAST** | Bandit (Python), Semgrep | CI on every PR | Block on HIGH severity |
| **SCA** | pip-audit (Python), npm audit (JS) | CI on every PR | Block on CRITICAL |
| **Container** | Trivy | CI on every PR | Block on CRITICAL unfixed |
| **Secrets** | detect-secrets | Pre-commit local | Block commit |
| **Cloud** | GCP Security Command Center | Continuous | Alert on CRITICAL/HIGH |

## Pre-commit Hooks (Local Development)

### Required Configuration

All repositories must include `.pre-commit-config.yaml`:

```yaml
repos:
  # Secret detection - MANDATORY
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: |
          (?x)^(
            .*\.lock$|
            .*package-lock\.json$|
            .*\.svg$|
            \.secrets\.baseline$
          )$

  # Standard checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-json

  # Conventional commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

### Developer Setup

```bash
# Install (one-time)
pip install pre-commit detect-secrets
pre-commit install
pre-commit install --hook-type commit-msg

# Create baseline for existing secrets (false positives)
detect-secrets scan > .secrets.baseline

# Run manually
pre-commit run --all-files
```

### Secrets Baseline

The `.secrets.baseline` file tracks known false positives (e.g., test API keys in example files). This file MUST be committed to version control.

## SAST (Static Application Security Testing)

### Python Services

Add to CI workflow:

```yaml
- name: Run Bandit security scanner
  run: |
    pip install bandit
    bandit -r app/ -ll -f json -o bandit-report.json || true
    bandit -r app/ -ll

- name: Run Semgrep SAST
  run: |
    pip install semgrep
    semgrep --config=auto app/ --json -o semgrep-report.json || true
    semgrep --config=auto app/
```

### JavaScript/TypeScript Services

```yaml
- name: Run ESLint security rules
  run: npm run lint

- name: Run Snyk SAST
  uses: snyk/actions/node@master
  with:
    args: --severity-threshold=high
```

## SCA (Software Composition Analysis)

### Python Services

```yaml
- name: Check Python dependencies
  run: |
    pip install pip-audit
    pip-audit --strict --desc on
```

### JavaScript Services

```yaml
- name: Audit npm dependencies
  run: npm audit --audit-level=high
```

## Container Scanning

### Required Trivy Configuration

Add to CI workflow for any service with a Dockerfile:

```yaml
container-security:
  name: Container Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        tags: ${{ github.repository }}:scan
        load: true

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@0.28.0
      with:
        image-ref: '${{ github.repository }}:scan'
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'
        exit-code: '0'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Fail on CRITICAL vulnerabilities
      uses: aquasecurity/trivy-action@0.28.0
      with:
        image-ref: '${{ github.repository }}:scan'
        format: 'table'
        severity: 'CRITICAL'
        exit-code: '1'
        ignore-unfixed: true
```

### Trivy Configuration

- **Severity:** CRITICAL, HIGH (report), CRITICAL (fail)
- **Ignore unfixed:** Yes (don't fail on vulnerabilities without patches)
- **Output:** SARIF for GitHub Security tab + table for console

## GCP Security Command Center

### Required APIs

Enable in GCP project:

```bash
gcloud services enable securitycenter.googleapis.com --project=employa-prod
gcloud services enable containerscanning.googleapis.com --project=employa-prod
gcloud services enable websecurityscanner.googleapis.com --project=employa-prod
```

### What It Monitors

- **Container Scanning:** Automatic vulnerability scanning for images in Artifact Registry
- **Security Health Analytics:** Misconfiguration detection for GCP resources
- **Event Threat Detection:** Suspicious activity monitoring

### Console Access

https://console.cloud.google.com/security/command-center?project=employa-prod

## Vulnerability Response SLA

| Severity | Response Time | Resolution Time |
|----------|---------------|-----------------|
| **CRITICAL** | 4 hours | 24 hours |
| **HIGH** | 24 hours | 7 days |
| **MEDIUM** | 7 days | 30 days |
| **LOW** | 30 days | 90 days |

## HIPAA Mapping

| Security Scan | HIPAA Requirement |
|---------------|-------------------|
| SAST | 164.308(a)(1) - Security Management |
| SCA | 164.308(a)(1) - Risk Analysis |
| Container | 164.312(a)(1) - Access Control |
| Secrets | 164.312(d) - Person/Entity Authentication |
| Cloud | 164.312(b) - Audit Controls |

## Compliance Checklist

Before deploying any service:

- [ ] Pre-commit hooks installed with detect-secrets
- [ ] `.secrets.baseline` committed
- [ ] SAST (Bandit/Semgrep) passing in CI
- [ ] SCA (pip-audit/npm audit) passing in CI
- [ ] Trivy container scanning in CI (if Dockerized)
- [ ] No CRITICAL vulnerabilities unfixed
- [ ] GCP Security Command Center enabled

## Reference Implementations

- **Python (Dave):** [Dave/.github/workflows/ci.yml](../../../Dave/.github/workflows/ci.yml)
- **Pre-commit:** [.pre-commit-config.yaml](../../../../.pre-commit-config.yaml)
- **GCP Setup:** [docs/security/GCP-SECURITY-COMMAND-CENTER.md](../../../../docs/security/GCP-SECURITY-COMMAND-CENTER.md)

## Related Standards

- [security-secrets.md](security-secrets.md) - Secrets management
- [ci-cd-deployment.md](../ci-cd-deployment.md) - CI/CD pipeline requirements
- [compliance/hipaa-compliance.md](../compliance/hipaa-compliance.md) - HIPAA requirements
