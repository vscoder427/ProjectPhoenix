# Warp Frontend - Observability Guide

**Purpose:** HIPAA-compliant error tracking, performance monitoring, and logging for warp-frontend

**Tools:** Sentry (errors + performance), Custom Logger (PHI redaction), Next.js Web Vitals

**Last Updated:** 2026-01-12

---

## Quick Start

### Development Setup

```bash
# Install dependencies (already done)
npm install @sentry/nextjs

# Add environment variables to .env.local
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ORG=your-org
SENTRY_PROJECT=warp-frontend
SENTRY_AUTH_TOKEN=your-auth-token
```

### Using the Logger

```typescript
import { logger } from '@/src/lib/logger';

// Log user action (automatically redacts PHI)
logger.logUserAction('click', 'SubmitButton', {
  duration: 150,
  statusCode: 200,
});

// Log API call
logger.logApiCall('POST', '/api/profile', 200, 250);

// Log error
try {
  // ...
} catch (error) {
  logger.logError(error as Error, 'ProfileForm', {
    statusCode: 500,
    errorCode: 'VALIDATION_ERROR',
  });
}
```

---

## Architecture

### Three Pillars of Observability

1. **Error Tracking (Sentry)**
   - Client-side errors (React errors, network failures)
   - Server-side errors (API errors, SSR failures)
   - Automatic PHI redaction via `beforeSend` hook

2. **Performance Monitoring (Sentry + Web Vitals)**
   - Core Web Vitals: LCP, FID, CLS, TTFB, FCP, INP
   - Transaction tracing (page loads, API calls)
   - Session Replay (with PHI masking)

3. **Structured Logging (Custom Logger)**
   - Allowlist-based PHI redaction
   - Consistent log format
   - Safe for external logging services

---

## HIPAA Compliance (CRITICAL)

### The Problem

Employa handles Protected Health Information (PHI):
- Recovery journey details (sobriety dates, milestones, notes)
- Contact information (email, phone, address)
- Employment history
- User-generated content (profiles, applications)

**HIPAA Rule:** PHI must NEVER be logged to external systems without explicit consent and proper safeguards.

### Our Solution: Defense in Depth

#### Layer 1: Allowlist-Based Logger
**File:** `src/lib/logger.ts`

**Principle:** Only log explicitly safe fields. Everything else is silently dropped.

**Safe Fields (exhaustive list):**
```typescript
const SAFE_FIELDS = new Set([
  'userId',       // Truncated to uuid-XXXXXXXX
  'timestamp',    // ISO 8601 format
  'eventType',    // Categorized event names
  'statusCode',   // HTTP status codes
  'errorCode',    // Application error codes
  'component',    // Component/module name
  'action',       // User action name
  'duration',     // Timing in ms
  'count',        // Numeric counts
]);
```

**Usage:**
```typescript
logger.info('User action', {
  userId: '12345678-1234-1234-1234-123456789012',
  email: 'user@example.com',  // Silently dropped
  name: 'John Doe',            // Silently dropped
  statusCode: 200,             // Logged
});

// Output:
// {
//   "level": "info",
//   "message": "User action",
//   "userId": "uuid-12345678",
//   "statusCode": 200,
//   "timestamp": "2026-01-12T12:00:00Z"
// }
```

#### Layer 2: Message Redaction
**File:** `src/lib/logger.ts` (`redactMessage` function)

**Patterns redacted:**
- Email addresses → `[EMAIL]`
- Phone numbers (all formats) → `[PHONE]`
- SSN patterns → `[SSN]`
- Credit card numbers → `[CC]`
- Names (when preceded by common patterns) → `[NAME]`
- Addresses → `[ADDRESS]`

**Example:**
```typescript
logger.error('Failed to process email user@example.com for John Doe');

// Output:
// "Failed to process email [EMAIL] for [NAME]"
```

#### Layer 3: Sentry `beforeSend` Hook
**Files:** `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`

**What it does:**
1. Redacts error messages using same patterns as logger
2. Strips query parameters from URLs (might contain PII)
3. Removes cookies and authorization headers
4. Deletes user context (email, name, etc.)
5. Redacts breadcrumbs (user actions)
6. Applies allowlist to extra context

**Example:**
```typescript
// Before beforeSend:
{
  message: "User user@example.com not found",
  request: {
    url: "/api/users?email=user@example.com",
    cookies: { session: "abc123" },
    headers: { authorization: "Bearer token" }
  },
  user: { email: "user@example.com", name: "John Doe" }
}

// After beforeSend:
{
  message: "User [EMAIL] not found",
  request: {
    url: "/api/users"
  }
  // user, cookies, headers removed
}
```

#### Layer 4: Sentry Session Replay Masking
**File:** `sentry.client.config.ts`

```typescript
integrations: [
  Sentry.replayIntegration({
    maskAllText: true,      // Mask all text content
    blockAllMedia: true,    // Block images/videos
  }),
]
```

All text in session replays is replaced with `***`, preventing PHI from being recorded.

---

## Sentry Configuration

### Environment Variables

**Required:**
```bash
# .env.local (development)
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ORG=your-org
SENTRY_PROJECT=warp-frontend
SENTRY_AUTH_TOKEN=your-auth-token  # For source maps
```

**Production (Vercel/Cloud Run):**
- Set same variables in deployment platform
- `SENTRY_AUTH_TOKEN` only needed for build step (source maps)

### Sentry Dashboard Setup

1. **Create Project**
   - Go to Sentry → Projects → Create Project
   - Platform: Next.js
   - Alert frequency: Real-time

2. **Configure Alerts**
   - Error Rate > 10/min → Email team
   - New issue in production → Slack notification
   - Performance degradation (LCP > 2.5s) → Warning

3. **Source Maps**
   - Automatically uploaded during build via `@sentry/nextjs`
   - Configured in `next.config.ts` with `widenClientFileUpload: true`

4. **Release Tracking**
   - Set `SENTRY_RELEASE` in CI/CD to Git commit SHA
   - Track which errors belong to which deployment

### Sample Rate Configuration

**Development:**
```typescript
tracesSampleRate: 1.0,           // 100% of transactions
replaysSessionSampleRate: 0.1,   // 10% of sessions
replaysOnErrorSampleRate: 1.0,   // 100% of error sessions
```

**Production (adjust for cost):**
```typescript
tracesSampleRate: 0.1,           // 10% of transactions
replaysSessionSampleRate: 0.01,  // 1% of sessions
replaysOnErrorSampleRate: 1.0,   // 100% of error sessions
```

---

## Web Vitals Monitoring

### What We Track

**File:** `src/components/web-vitals.tsx`

- **LCP (Largest Contentful Paint):** Time until largest element renders
  - Target: < 2.5s (good), < 4s (needs improvement), > 4s (poor)
- **FID (First Input Delay):** Time from user interaction to browser response
  - Target: < 100ms (good), < 300ms (needs improvement), > 300ms (poor)
- **CLS (Cumulative Layout Shift):** Visual stability (unexpected layout shifts)
  - Target: < 0.1 (good), < 0.25 (needs improvement), > 0.25 (poor)
- **TTFB (Time to First Byte):** Server response time
  - Target: < 800ms (good), < 1800ms (needs improvement), > 1800ms (poor)
- **FCP (First Contentful Paint):** Time until first content renders
  - Target: < 1.8s (good), < 3s (needs improvement), > 3s (poor)
- **INP (Interaction to Next Paint):** Overall responsiveness
  - Target: < 200ms (good), < 500ms (needs improvement), > 500ms (poor)

### How It Works

```typescript
// src/components/web-vitals.tsx
useReportWebVitals((metric) => {
  // Send to Sentry
  Sentry.metrics.distribution(metric.name, metric.value, {
    unit: 'millisecond',
    tags: { rating: metric.rating },
  });

  // Optionally send to custom analytics
  // fetch('/api/analytics/web-vitals', { ... });
});
```

**Rendered in:**
```tsx
// app/layout.tsx
<body>
  <WebVitals />
  {children}
</body>
```

### Viewing Metrics

**Sentry Dashboard:**
1. Navigate to Performance → Web Vitals
2. Filter by page, country, browser
3. View percentiles (p50, p75, p95)
4. Set up alerts for degradation

**Custom Analytics (future):**
- Build `/api/analytics/web-vitals` endpoint
- Store in Supabase or GCP BigQuery
- Visualize in Grafana/Looker

---

## Custom Logger API

### Logger Methods

#### `logger.info(message, context?)`
General informational logs.

```typescript
logger.info('User profile loaded', {
  userId: 'user-123',
  component: 'ProfilePage',
  duration: 250,
});
```

#### `logger.warn(message, context?)`
Warning-level logs (non-critical issues).

```typescript
logger.warn('Retry attempt', {
  component: 'ApiClient',
  count: 3,
  statusCode: 429,
});
```

#### `logger.error(message, context?)`
Error-level logs (failures, exceptions).

```typescript
logger.error('Database query failed', {
  component: 'UserService',
  errorCode: 'DB_TIMEOUT',
  statusCode: 500,
});
```

#### `logger.debug(message, context?)`
Debug logs (only in development).

```typescript
logger.debug('State update', {
  component: 'FormField',
  action: 'onChange',
});
```

#### `logger.logUserAction(action, component, context?)`
Track user interactions.

```typescript
logger.logUserAction('click', 'SubmitButton', {
  duration: 150,
  eventType: 'form_submission',
});
```

#### `logger.logApiCall(method, path, statusCode, duration)`
Track API calls (automatically strips query params).

```typescript
logger.logApiCall('POST', '/api/profile?email=user@example.com', 200, 350);

// Output:
// {
//   "eventType": "api_call",
//   "component": "POST /api/profile",
//   "statusCode": 200,
//   "duration": 350
// }
```

#### `logger.logError(error, component?, context?)`
Log JavaScript Error objects.

```typescript
try {
  throw new Error('Validation failed for email user@example.com');
} catch (error) {
  logger.logError(error as Error, 'FormField', {
    statusCode: 400,
    errorCode: 'VALIDATION_ERROR',
  });
}

// Output:
// {
//   "level": "error",
//   "message": "Validation failed for email [EMAIL]",
//   "component": "FormField",
//   "errorCode": "Error",
//   "statusCode": 400
// }
```

---

## Testing PHI Redaction

### Unit Tests

**File:** `src/lib/logger.test.ts`

**Run tests:**
```bash
npm test -- logger.test.ts
```

**Coverage:**
- ✅ Allowlist enforcement (safe fields only)
- ✅ Message redaction (email, phone, SSN, CC, names, addresses)
- ✅ Context stripping (unsafe fields dropped)
- ✅ Logger methods (info, error, logUserAction, logApiCall, logError)

**Example test:**
```typescript
it('strips all non-safe fields', () => {
  const context = {
    email: 'user@example.com',
    name: 'John Doe',
    statusCode: 200, // Safe field
  };

  const result = redactContext(context);

  expect(result.statusCode).toBe(200);
  expect(result).not.toHaveProperty('email');
  expect(result).not.toHaveProperty('name');
});
```

### Manual Testing

**Test PHI redaction before production:**

```typescript
// Test email redaction
logger.info('Testing email: user@example.com', { statusCode: 200 });
// Expected: "Testing email: [EMAIL]"

// Test phone redaction
logger.info('Call 555-123-4567', { statusCode: 200 });
// Expected: "Call [PHONE]"

// Test allowlist
logger.info('Test', {
  email: 'user@example.com',  // Should be dropped
  name: 'John Doe',            // Should be dropped
  statusCode: 200,             // Should be kept
});
// Expected: { statusCode: 200, timestamp: "..." } (email and name absent)
```

**Verify Sentry `beforeSend`:**
1. Trigger an error with PHI in message
2. Check Sentry dashboard
3. Confirm message is redacted

---

## Common Patterns

### Pattern 1: Form Submission
```typescript
async function handleSubmit(formData: FormData) {
  const startTime = performance.now();

  try {
    const response = await fetch('/api/profile', {
      method: 'POST',
      body: formData,
    });

    const duration = performance.now() - startTime;

    logger.logApiCall('POST', '/api/profile', response.status, duration);

    if (!response.ok) {
      logger.warn('Form submission failed', {
        component: 'ProfileForm',
        statusCode: response.status,
        errorCode: 'SUBMIT_FAILED',
      });
    }
  } catch (error) {
    logger.logError(error as Error, 'ProfileForm', {
      statusCode: 500,
      errorCode: 'NETWORK_ERROR',
    });
  }
}
```

### Pattern 2: User Interaction Tracking
```typescript
function trackButtonClick(buttonName: string) {
  logger.logUserAction('click', buttonName, {
    eventType: 'button_click',
  });
}

// Usage
<Button onClick={() => trackButtonClick('SubmitButton')}>
  Submit
</Button>
```

### Pattern 3: Performance Monitoring
```typescript
const startTime = performance.now();

await heavyOperation();

const duration = performance.now() - startTime;

logger.info('Operation completed', {
  component: 'DataProcessor',
  duration,
  count: processedItems,
});
```

---

## Production Deployment

### Checklist

- [ ] Set `NEXT_PUBLIC_SENTRY_DSN` in environment
- [ ] Set `SENTRY_ORG`, `SENTRY_PROJECT`, `SENTRY_AUTH_TOKEN` for build
- [ ] Adjust sample rates for cost control
- [ ] Configure Sentry alerts (email, Slack)
- [ ] Test PHI redaction with production data
- [ ] Verify source maps are uploaded
- [ ] Set up release tracking (`SENTRY_RELEASE` = Git SHA)

### Monitoring Dashboard

**Sentry:**
- Errors: https://sentry.io/organizations/your-org/issues/
- Performance: https://sentry.io/organizations/your-org/performance/
- Releases: https://sentry.io/organizations/your-org/releases/

**Next.js:**
- Vercel Analytics (if deployed to Vercel)
- Cloud Run Metrics (if deployed to Cloud Run)

---

## Troubleshooting

### Issue: Logs contain PHI

**Cause:** Field not in `SAFE_FIELDS` allowlist but being logged

**Solution:**
1. Check `src/lib/logger.ts` → `SAFE_FIELDS`
2. Verify field is NOT in allowlist
3. If field should be safe, add to allowlist (rare - must justify)
4. If field contains PHI, ensure it's NOT in allowlist (correct behavior)

### Issue: Sentry errors not appearing

**Cause:** Missing `NEXT_PUBLIC_SENTRY_DSN`

**Solution:**
```bash
# .env.local
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

Restart dev server: `npm run dev`

### Issue: Source maps not uploaded

**Cause:** Missing `SENTRY_AUTH_TOKEN` or `SENTRY_ORG`/`SENTRY_PROJECT`

**Solution:**
```bash
# .env.local
SENTRY_ORG=your-org
SENTRY_PROJECT=warp-frontend
SENTRY_AUTH_TOKEN=your-token  # From Sentry → Settings → Auth Tokens
```

### Issue: Web Vitals not reporting

**Cause:** `WebVitals` component not rendered

**Solution:** Verify `app/layout.tsx` includes:
```tsx
<body>
  <WebVitals />
  {children}
</body>
```

---

## Best Practices

### ✅ Do

1. **Always use the custom logger** instead of `console.log`
2. **Trust the allowlist** - only safe fields are logged
3. **Test PHI redaction** before deploying new logging code
4. **Monitor Sentry alerts** - don't ignore error spikes
5. **Review logs periodically** - ensure no PHI leaked
6. **Use structured logging** - pass context objects, not string interpolation
7. **Set up alerts** - know when errors occur in production

### ❌ Don't

1. **Never bypass the logger** with direct `console.log` in production
2. **Never add PII/PHI fields to `SAFE_FIELDS`** without legal review
3. **Never log user-generated content** (notes, messages, etc.)
4. **Never disable `beforeSend` hook** - it's the last line of defense
5. **Don't log passwords, tokens, or API keys** (obviously)
6. **Don't ignore Sentry errors** - each one is a real user problem
7. **Don't sample too aggressively** - you'll miss critical errors

---

## Resources

- **Sentry Docs:** https://docs.sentry.io/platforms/javascript/guides/nextjs/
- **Next.js Web Vitals:** https://nextjs.org/docs/app/api-reference/functions/use-report-web-vitals
- **HIPAA Compliance:** https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html
- **Web Vitals:** https://web.dev/vitals/

---

## Next Steps

### Phase 1 (Current) ✅
- [x] Install Sentry
- [x] Configure PHI redaction (client + server + edge)
- [x] Build custom logger with allowlist
- [x] Add Web Vitals tracking
- [x] Write PHI redaction tests
- [x] Document observability patterns

### Phase 2 (Auth UI)
- [ ] Add error tracking for login/register flows
- [ ] Monitor authentication API performance
- [ ] Track form validation errors
- [ ] Set up alerts for auth failures

### Phase 3 (Job Search UI)
- [ ] Track job search performance
- [ ] Monitor application submission flows
- [ ] Add custom metrics (searches/day, applications/user)
- [ ] Performance testing (LCP for job listings)
