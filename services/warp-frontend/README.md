# Warp Frontend - Firebase Hosting Spike

**Purpose:** Validate Firebase Hosting can support Next.js 15 App Router SSR with GCP Secret Manager integration (ADR-0001).

## Spike Results - ✅ SUCCESSFUL

**Date:** 2026-01-12
**Status:** All critical requirements validated
**Live URL:** https://gen-lang-client-0011584621.web.app

### What Was Tested

1. ✅ **Next.js 15 App Router** - Server-side rendering works perfectly
2. ✅ **GCP Secret Manager** - Server components can access secrets with proper IAM
3. ✅ **Firebase Hosting + Cloud Functions** - Automatic SSR deployment via Cloud Functions
4. ✅ **Dynamic Rendering** - `export const dynamic = 'force-dynamic'` prevents static generation

## Spike Details

- **Issue:** [#343](https://github.com/employa-work/employa-web/issues/343)
- **Epic:** [#327](https://github.com/employa-work/employa-web/issues/327) (Phase 1 Pre-Development)
- **Firebase Project:** gen-lang-client-0011584621
- **Region:** us-central1

## Project Structure

```
warp-frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Homepage with SSR + Secret Manager test
│   └── globals.css         # Global styles
├── firebase.json           # Firebase Hosting config
├── .firebaserc             # Firebase project config
└── package.json            # Dependencies
```

## Local Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Deploy to Firebase

```bash
npm run build
firebase deploy --only hosting
```

## Results Summary

### ✅ Technical Validation

- [x] **Page renders server-side** - Confirmed via server timestamp in HTML source
- [x] **Secret Manager integration** - Server components can access GCP secrets
- [x] **IAM configuration** - Granted `roles/secretmanager.secretAccessor` to Compute Engine SA
- [x] **Deployment process** - Simple `firebase deploy --only hosting` workflow
- [ ] **Performance benchmarks** - TTFB/FCP not yet measured (needs Lighthouse audit)

### Key Learnings

**Firebase Hosting for Next.js SSR:**
- Uses Cloud Functions under the hood (same runtime environment as Cloud Run)
- Requires identical IAM setup to Cloud Run (Secret Manager permissions)
- Auto-detects Next.js and configures Cloud Functions automatically
- ~2 minute deployment time
- Built-in preview deployments available

**IAM Setup Required:**
```bash
# Grant Secret Manager access to Compute Engine service account
gcloud projects add-iam-policy-binding gen-lang-client-0011584621 \
  --member="serviceAccount:359184175915-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None
```

**Dynamic Rendering:**
```typescript
// Force runtime rendering (disable static generation)
export const dynamic = 'force-dynamic';
```

### Trade-offs vs Cloud Run + CDN

**Advantages:**
- ✅ Simpler deployment (single command)
- ✅ Built-in preview deployments
- ✅ Automatic Next.js detection and configuration

**Disadvantages:**
- ⚠️ Less control over Cloud Function configuration (memory, CPU, timeout)
- ⚠️ Requires Firebase CLI (different tooling from gcloud)
- ⚠️ Different deployment pattern than other Employa services (7 services on Cloud Run)

## Recommendation

**Firebase Hosting works perfectly for Next.js 15 SSR + Secret Manager.**

However, for Employa's architecture, **Cloud Run + CDN may be preferred** for:
1. Consistency with existing 7 Cloud Run services
2. Standard GCP tooling (gcloud vs Firebase CLI)
3. Full control over compute resources
4. Unified deployment patterns

## Next Steps

1. Run Lighthouse performance audit
2. Compare with Cloud Run + CDN deployment
3. Document final decision in ADR-0001
