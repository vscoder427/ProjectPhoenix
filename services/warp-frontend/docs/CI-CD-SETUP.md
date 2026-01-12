# CI/CD Setup - Warp Frontend

**Status:** Week 1 Implementation Complete
**Date:** 2026-01-12
**Related ADR:** [ADR-0006: Authentication & Token Storage](adr/0006-authentication-token-storage.md)
**GitHub Issue:** [#349](https://github.com/employa-work/employa-web/issues/349)

---

## Overview

This document describes the CI/CD infrastructure for warp-frontend, implemented as part of Phase 2 - Foundation (Week 1).

### Architecture

```
┌─────────────────┐
│  Pull Request   │
│   or Push       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ CI Pipeline (.github/workflows/ci.yml)                  │
├─────────────────────────────────────────────────────────┤
│ 1. Lint & Type Check  (ESLint + TypeScript)            │
│ 2. Unit Tests         (Jest with 85% coverage)         │
│ 3. Security Scan      (npm audit + Snyk)               │
│ 4. Build Validation   (Next.js build)                  │
│ 5. E2E Tests          (Playwright - PR only)           │
│ 6. CI Success         (Summary + PR comment)           │
└─────────────────────────────────────────────────────────┘
         │
         ▼ (on success)
┌─────────────────────────────────────────────────────────┐
│ Deploy Pipeline (.github/workflows/deploy-staging.yml) │
├─────────────────────────────────────────────────────────┤
│ 1. Pre-Deploy Checks  (Secrets + CI status)            │
│ 2. Deploy to Vercel   (Staging environment)            │
│ 3. Verify Deployment  (Health check)                   │
│ 4. Success Notify     (PR/commit comment)              │
└─────────────────────────────────────────────────────────┘
```

---

## CI Pipeline

**File:** `.github/workflows/ci.yml`

### Jobs

1. **lint-and-typecheck**
   - Runs ESLint
   - Runs TypeScript type checker (`tsc --noEmit`)
   - Fast fail for syntax/type errors

2. **test**
   - Runs Jest unit and component tests
   - Generates coverage report
   - Enforces 85% coverage threshold (ProjectPhoenix standard)
   - Uploads coverage to Codecov

3. **security-scan**
   - Runs `npm audit` (high severity threshold)
   - Runs Snyk security scan
   - Non-blocking (warnings only)

4. **build-validation**
   - Builds Next.js application
   - Validates build succeeds
   - Uploads build artifacts (7-day retention)

5. **e2e-tests** (PR only)
   - Installs Playwright browsers
   - Runs E2E test suite
   - Uploads report on failure

6. **ci-success** (Summary)
   - Checks all job statuses
   - Comments on PR with results
   - Required status check for merge

### Environment Variables (CI)

```yaml
NODE_VERSION: "22.x"              # ProjectPhoenix standard
COVERAGE_THRESHOLD: 85            # ProjectPhoenix standard
```

### Secrets Required

- `SNYK_TOKEN` - Snyk API token for security scanning
- `CODECOV_TOKEN` - Codecov upload token (optional)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL (for build)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key (for build)

---

## Deploy Pipeline

**File:** `.github/workflows/deploy-staging.yml`

### Triggers

- Push to `main` or `develop` branches
- Manual workflow dispatch

### Jobs

1. **pre-deploy-checks**
   - Validates required secrets exist
   - Checks CI pipeline status for commit
   - Fails fast if CI didn't pass

2. **deploy-staging**
   - Installs Vercel CLI
   - Pulls Vercel environment config
   - Builds project artifacts
   - Deploys to Vercel (preview/staging)
   - Comments deployment URL on PR/commit

3. **verify-deployment**
   - Waits 30s for deployment propagation
   - Performs health check (5 retries)
   - Placeholder for Lighthouse CI (future)

4. **deployment-success**
   - Prints summary
   - Outputs deployment URL

### Environment Variables (Deploy)

```yaml
NODE_VERSION: "22.x"
VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Secrets Required

- `VERCEL_TOKEN` - Vercel CLI token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID

---

## Secrets Management

### Migration to GCP Secret Manager

**Script:** `scripts/migrate-secrets-to-gcp.ps1`

#### Usage

```powershell
# Dry run (preview)
.\scripts\migrate-secrets-to-gcp.ps1 -DryRun

# Migrate to production project
.\scripts\migrate-secrets-to-gcp.ps1 -ProjectId employa-production

# Force overwrite existing secrets
.\scripts\migrate-secrets-to-gcp.ps1 -ProjectId employa-production -Force
```

#### Secrets Migrated (13 total)

**Supabase (Warp Database - Shared):**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

**Dave API:**
- `DAVE_API_URL`
- `DAVE_API_KEY` (optional - may use JWT)

**Google Gemini AI:**
- `GEMINI_API_KEY`

**NextAuth.js:**
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`

**Google OAuth:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

**Vercel (CI/CD):**
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

#### Post-Migration Steps

1. **Grant Cloud Run access:**
   ```bash
   gcloud secrets add-iam-policy-binding <SECRET_NAME> \
     --member="serviceAccount:<SERVICE_ACCOUNT>" \
     --role="roles/secretmanager.secretAccessor" \
     --project="employa-production"
   ```

2. **Add GitHub Actions secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `SNYK_TOKEN`

3. **Update warp-frontend production config:**
   - Load secrets from GCP Secret Manager (not `.env.workspace`)
   - Use `@google-cloud/secret-manager` library

4. **Test staging deployment:**
   - Push to `develop` branch
   - Verify deployment succeeds
   - Check secrets loaded correctly

---

## Local Development

### Prerequisites

- Node.js 22.x
- npm (comes with Node.js)
- `.env.workspace` configured at workspace root

### Setup

```bash
cd ProjectPhoenix/services/warp-frontend

# Install dependencies
npm ci

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build

# Run E2E tests
npm run test:e2e
```

### Pre-commit Hooks

**TODO:** Set up Husky + lint-staged for pre-commit checks
- ESLint auto-fix
- TypeScript type check
- Jest unit tests (fast subset)

---

## Troubleshooting

### CI Pipeline Failures

**Lint errors:**
```bash
npm run lint:fix  # Auto-fix ESLint issues
```

**Type errors:**
```bash
npx tsc --noEmit  # See all type errors
```

**Test failures:**
```bash
npm run test:watch  # Interactive test runner
```

**Coverage below threshold:**
```bash
npm run test:coverage  # See coverage report
# Add more tests for uncovered files
```

### Deployment Failures

**Vercel token invalid:**
- Regenerate token at https://vercel.com/account/tokens
- Update `VERCEL_TOKEN` in GitHub Actions secrets

**Build fails:**
- Check required environment variables are set
- Ensure `.env.workspace` has all secrets
- Run local build: `npm run build`

**Health check fails:**
- Check Vercel deployment logs
- Verify secrets loaded correctly
- Check Next.js server logs

---

## Verification Checklist

Week 1 acceptance criteria from [#349](https://github.com/employa-work/employa-web/issues/349):

### CI/CD Pipeline (Warp)
- [x] Create `.github/workflows/ci.yml` - Lint, test, build, contract tests
- [x] Create `.github/workflows/deploy-staging.yml` - Automated Vercel staging deploy
- [x] Pipeline runs on PR creation and merge to main (TESTING IN PROGRESS)
- [ ] All checks must pass before merge (required status checks)

### Secrets Migration
- [x] Create `scripts/migrate-secrets-to-gcp.ps1` - One-time GCP Secret Manager migration script
- [ ] Migrate 13 secrets from `.env.workspace` to GCP Secret Manager (requires manual execution)
- [ ] Update Warp to load secrets from GCP in production (Week 2-3)
- [ ] Verify no `.env.workspace` secrets in production deployments (Week 2-3)

### Verification
- [ ] Warp CI pipeline passes (lint, test, build, contract tests) - Requires PR
- [ ] Staging auto-deploys on merge to main - Requires merge
- [ ] Services load secrets from GCP (no hardcoded credentials) - Week 2-3

---

## Next Steps (Week 2-3)

1. **Test CI pipeline:**
   - Create PR with workflow files
   - Verify all jobs pass
   - Check PR comments

2. **Configure GitHub Actions secrets:**
   - Add required secrets to repo
   - Test deployment workflow

3. **Migrate secrets:**
   - Run migration script
   - Grant Cloud Run access
   - Update warp-frontend to load from GCP

4. **Enable required status checks:**
   - Go to repo Settings → Branches
   - Require "CI Success" check to pass

5. **Authentication migration (Week 2-3):**
   - Implement httpOnly cookies (ADR-0006)
   - JWT admin auth consolidation (ADR-0007)

---

## References

- **ADR-0006:** [Authentication & Token Storage](adr/0006-authentication-token-storage.md)
- **GitHub Issue:** [#349 - Week 1: CI/CD Infrastructure](https://github.com/employa-work/employa-web/issues/349)
- **Phase 2 Epic:** [#328 - Phase 2: Foundation](https://github.com/employa-work/employa-web/issues/328)
- **ProjectPhoenix Standards:** `ProjectPhoenix/docs/standards/`
- **Dave CI/CD (Gold Standard):** `Dave/.github/workflows/ci.yml`
