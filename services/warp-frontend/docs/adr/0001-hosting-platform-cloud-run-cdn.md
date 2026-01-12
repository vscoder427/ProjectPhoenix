# ADR-0001: Hosting Platform - Cloud Run + CDN

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#343](https://github.com/employa-work/employa-web/issues/343)
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Context

Employa's new web frontend (warp-frontend) needs a hosting platform that supports:
- Next.js 15 App Router with server-side rendering (SSR)
- GCP Secret Manager integration for sensitive configuration
- Preview deployments for PR testing
- Low latency for job seekers and employers
- Cost-effective scaling from MVP to production

Two primary options were evaluated:
1. **Firebase Hosting** (with Cloud Functions for SSR)
2. **Cloud Run + Cloud CDN** (containerized Next.js app)

---

## Decision

**We will use Cloud Run + Cloud CDN** for warp-frontend hosting.

---

## Rationale

### Firebase Hosting Spike Results

A technical spike ([#343](https://github.com/employa-work/employa-web/issues/343)) validated Firebase Hosting **works perfectly** for our requirements:

✅ **Technical Validation:**
- Next.js 15 App Router SSR: **Works**
- Secret Manager integration: **Works** (with IAM setup)
- Deployment: **Simple** (`firebase deploy --only hosting`)
- Auto-configuration: **Excellent** (auto-detects Next.js, creates Cloud Functions)

⚠️ **Trade-offs:**
- Uses Cloud Functions under the hood (same runtime as Cloud Run)
- Requires Firebase CLI (different from `gcloud`)
- Less control over function configuration (memory, CPU, timeout)
- Next.js support is **preview-stage** (may have breaking changes)

**Spike Demo:** https://gen-lang-client-0011584621.web.app
**Spike Code:** `ProjectPhoenix/services/warp-frontend/`

### Why Cloud Run + CDN Wins

**1. Architectural Consistency**
- 7 Employa services already on Cloud Run:
  - `dave-service` (recovery chatbot)
  - `aa-meetings-api` (meeting search)
  - `outreach-api`, `user-onboarding-api`, `career-tools-api`, etc.
- **Single deployment pattern** across all services (backend + frontend)
- Reduces cognitive load for team (one way to deploy, not two)

**2. Tooling Standardization**
- **Cloud Run**: Standard `gcloud` CLI workflow
  - `gcloud run deploy --image=... --region=us-central1`
  - Integrated with existing CI/CD (GitHub Actions + Cloud Build)
  - Same IAM patterns as backend services
- **Firebase Hosting**: Requires Firebase CLI
  - Different tooling, different mental model
  - Adds complexity to deployment scripts

**3. Production Control**
- **Cloud Run**: Full configuration control
  - Memory: 512Mi - 32Gi (tune for Next.js SSR workload)
  - CPU: 1-8 vCPUs (scale for traffic spikes)
  - Timeout: Up to 60 minutes (long-running API calls if needed)
  - Concurrency: 1-1000 requests per instance
  - Min/max instances: Fine-grained autoscaling
- **Firebase Hosting**: Limited Cloud Function config
  - Abstracted configuration (less control)
  - Preview-stage support (potential breaking changes)

**4. Platform Maturity**
- **Cloud Run**: Generally Available (GA), production-grade
- **Firebase Next.js support**: Preview-stage (as of 2026-01)
  - Firebase docs warn: "breaking changes can be expected"
  - Risk of future migration work if Firebase changes Next.js integration

**5. Cost Predictability**
- **Cloud Run + CDN**: Clear pricing model
  - Cloud Run: Pay per request + CPU/memory usage
  - Cloud CDN: Pay per GB egress (cache static assets)
  - Same billing as other services (unified cost tracking)
- **Firebase Hosting**: Bundled pricing
  - 10GB storage, 360MB/day transfer on free tier
  - Overages charged separately
  - Cloud Functions billing mixed with Hosting

---

## Alternatives Considered

### Option 1: Firebase Hosting ❌

**Pros:**
- ✅ Simpler initial deployment (`firebase deploy`)
- ✅ Built-in preview deployments (Firebase Hosting feature)
- ✅ Automatic Next.js detection
- ✅ Integrated with Firebase ecosystem (if using Firestore, Auth)

**Cons:**
- ❌ Different deployment pattern than 7 existing services
- ❌ Requires Firebase CLI (not `gcloud`)
- ❌ Less control over Cloud Function configuration
- ❌ Preview-stage Next.js support (risk of breaking changes)
- ❌ Would be the **only** service not on Cloud Run

**Verdict:** Technically viable but architecturally inconsistent.

### Option 2: Cloud Run + Cloud CDN ✅ **CHOSEN**

**Pros:**
- ✅ Consistent with 7 existing Cloud Run services
- ✅ Standard `gcloud` workflow (team already knows it)
- ✅ Full control over memory, CPU, timeout, autoscaling
- ✅ Production-grade (Cloud Run is GA)
- ✅ Unified deployment patterns (backend + frontend)
- ✅ Same IAM patterns as backend services

**Cons:**
- ⚠️ Requires containerization (Dockerfile for Next.js)
- ⚠️ More configuration than Firebase (CDN setup, cache rules)
- ⚠️ Preview deployments need manual setup (not built-in)

**Verdict:** More initial setup, but better long-term architecture.

### Option 3: Vercel ❌

**Pros:**
- ✅ Built by Next.js creators (best Next.js support)
- ✅ Zero-config deployment
- ✅ Excellent preview deployments

**Cons:**
- ❌ Higher cost at scale ($20/user/month for team features)
- ❌ Vendor lock-in (proprietary platform)
- ❌ Secret Manager integration requires workarounds
- ❌ No GCP integration (different cloud provider)

**Verdict:** Rejected due to cost and GCP integration requirements.

---

## Implementation Plan

### Phase 1: Containerize Next.js App
- Create `Dockerfile` for Next.js 15 (standalone build)
- Configure `.dockerignore` (exclude node_modules, .next, etc.)
- Test local build: `docker build -t warp-frontend .`

### Phase 2: Cloud Run Deployment
- Create Cloud Run service: `warp-frontend`
- Region: `us-central1` (same as backend services)
- Configure environment variables (Supabase, Gemini API, etc.)
- Grant Secret Manager access to Cloud Run SA
- Deploy: `gcloud run deploy warp-frontend --image=...`

### Phase 3: Cloud CDN Setup
- Create Cloud Load Balancer (HTTPS)
- Backend: Cloud Run service (warp-frontend)
- Enable Cloud CDN for static assets (/_next/static/*, /images/*)
- Configure cache rules (1 year for immutable assets, no-cache for HTML)
- SSL certificate: Managed certificate for `employa.work`

### Phase 4: CI/CD Automation
- GitHub Actions workflow:
  1. Build Docker image (Cloud Build)
  2. Push to Artifact Registry
  3. Deploy to Cloud Run
  4. Invalidate CDN cache (if needed)
- Preview deployments: Deploy PRs to separate Cloud Run services

### Phase 5: Monitoring
- Cloud Logging: Application logs, request logs
- Cloud Monitoring: Latency (p50, p95, p99), error rate, request count
- Alerting: p95 latency > 1s, error rate > 1%

---

## Consequences

### Positive

1. **Unified Architecture**: All 8 Employa services (7 backend + 1 frontend) on Cloud Run
2. **Standard Tooling**: Single `gcloud` workflow for all deployments
3. **Production Control**: Full configuration of memory, CPU, timeout, autoscaling
4. **Team Knowledge**: Leverage existing Cloud Run expertise
5. **Cost Visibility**: Frontend costs tracked alongside backend costs

### Negative

1. **Initial Setup Effort**: Requires Dockerfile, CDN config, LB setup (~4-8 hours)
2. **Preview Deployments**: Not built-in (need to build custom solution)
3. **Configuration Complexity**: More knobs to tune vs Firebase auto-config

### Neutral

1. **IAM Setup**: Same Secret Manager permissions needed (Firebase and Cloud Run identical)
2. **Performance**: Both options use Cloud Functions/Cloud Run (similar latency)

---

## Success Metrics

### Performance Targets
- **TTFB (Time to First Byte):** < 800ms (p95)
- **FCP (First Contentful Paint):** < 1.5s (p95)
- **LCP (Largest Contentful Paint):** < 2.5s (p95)
- **CLS (Cumulative Layout Shift):** < 0.1
- **CDN Cache Hit Rate:** > 80% for static assets

### Operational Targets
- **Deploy Time:** < 5 minutes (build + deploy)
- **Rollback Time:** < 2 minutes (revert to previous revision)
- **Uptime:** 99.9% (Cloud Run SLA)

---

## References

- **Spike Issue:** [#343](https://github.com/employa-work/employa-web/issues/343) - Firebase Hosting Spike
- **Epic Issue:** [#327](https://github.com/employa-work/employa-web/issues/327) - Phase 1 Pre-Development
- **Spike Demo:** https://gen-lang-client-0011584621.web.app
- **Spike Code:** `ProjectPhoenix/services/warp-frontend/`
- **Cloud Run Docs:** https://cloud.google.com/run/docs
- **Cloud CDN Docs:** https://cloud.google.com/cdn/docs
- **Next.js Docs:** https://nextjs.org/docs/deployment#self-hosting

---

## Notes

- Firebase Hosting remains a **valid option** if architectural consistency becomes less important
- This decision can be revisited if:
  - Firebase Next.js support reaches GA status
  - Employa moves all services to Firebase (unlikely)
  - Cloud Run costs become prohibitive (also unlikely)
- The Firebase spike code is preserved in `ProjectPhoenix/services/warp-frontend/` as reference
