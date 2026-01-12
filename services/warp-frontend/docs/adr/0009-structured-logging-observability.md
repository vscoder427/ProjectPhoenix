# ADR-0009: Structured Logging & Observability

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#328](https://github.com/employa-work/employa-web/issues/328)
**Epic:** [#328](https://github.com/employa-work/employa-web/issues/328) - Phase 2 Foundation

---

## Context

Employa needs production-grade logging and observability for:
- **Debugging:** Trace user issues across frontend + backend (distributed tracing)
- **Monitoring:** Track errors, performance, user behavior
- **Compliance:** HIPAA requires audit logs with PHI protection (6-year retention)
- **Operations:** Monitor service health, detect anomalies, alerting

Current state:
- **Warp (Next.js):** Mix of `console.log()` and custom logger utility (inconsistent)
- **Dave (FastAPI):** Structured logging with `structlog` (no PHI redaction)
- **No correlation:** Cannot trace requests across services (no trace IDs)
- **PHI exposure risk:** Logs may contain emails, recovery status, chat messages

Three key decisions needed:
1. **Logging Framework:** Which logger for Warp (Winston vs Pino)?
2. **PHI Redaction:** Where to redact PHI (client, server, both)?
3. **Log Structure:** What fields should every log entry have?

---

## Decision

**We will use Pino (Warp) + Structlog (Dave) with defense-in-depth PHI redaction and minimal core log structure.**

### Logging Framework
- **Warp (Next.js):** Pino (JSON-first, fast, GCP Cloud Logging compatible)
- **Dave (Python):** Structlog (already in use, add PHI redaction processor)
- **Format:** JSON structured logs with standardized fields

### PHI Redaction Strategy (Defense in Depth)
- **Client-side (Warp):** Redact before logging (prevents PHI in browser console, Sentry)
- **Server-side (Services):** Redact in log formatter (prevents PHI in Cloud Logging)
- **Redacted fields:** emails, names, phones, recovery status, chat messages, applications

### Log Structure (Minimal Core Fields)
```typescript
interface LogEntry {
  timestamp: string;        // ISO8601 (e.g., "2026-01-12T10:30:00Z")
  level: "info" | "warn" | "error" | "debug";
  service: "warp-frontend" | "dave-service" | "aameetings-api";
  traceId: string;          // For distributed tracing (correlationId)
  userId?: string;          // Hashed SHA-256 (not raw email)
  message: string;
  context?: object;         // Feature-specific data (optional)
}
```

### GCP Integration
- **Cloud Logging:** Automatic ingestion of JSON logs from Cloud Run
- **Error Reporting:** Errors with `severity: ERROR` auto-create Error Reporting entries
- **Trace Correlation:** `traceId` field links frontend + backend logs

---

## Rationale

### Logging Framework Choice

**Why Pino for Warp (Next.js):**

**1. Performance**

| Framework | Throughput | Overhead | Bundle Size |
|-----------|------------|----------|-------------|
| Pino | 100k+ logs/sec | <1ms | 15KB |
| Winston | 20k logs/sec | ~5ms | 45KB |
| Bunyan | 30k logs/sec | ~3ms | 30KB |

**Frontend impact:** Pino has smallest bundle size (better for page load performance)

**2. JSON-First Output**

**Pino (native JSON):**
```json
{
  "timestamp": "2026-01-12T10:30:00Z",
  "level": "info",
  "service": "warp-frontend",
  "traceId": "abc123",
  "message": "User logged in"
}
```

**Winston (needs configuration):**
```javascript
// Requires custom formatter to output JSON
const winston = require('winston');
winston.format.combine(
  winston.format.timestamp(),
  winston.format.json()
);
```

**Why JSON matters:** GCP Cloud Logging ingests JSON natively (no parsing needed)

**3. Next.js Ecosystem Standard**

- ✅ Vercel recommends Pino for Next.js
- ✅ Large ecosystem (pino-http, pino-pretty, pino-sentry)
- ✅ Used by Next.js core team

**4. Consistency with Backend**

**Backend (Dave):** Structlog outputs JSON
**Frontend (Warp):** Pino outputs JSON
**Result:** Unified log format across all services (easier to query in Cloud Logging)

**Why keep Structlog for Dave (Python):**

- ✅ Already implemented in Dave
- ✅ Python standard for structured logging
- ✅ No migration needed (add PHI redaction processor only)

### PHI Redaction Strategy

**Why defense in depth (client + server):**

**Layer 1: Client-Side Redaction (Warp)**

```typescript
// Warp/src/lib/logger-redaction.ts
logger.info({
  email: 'user@example.com',  // Redacted to [REDACTED]
  message: 'User in recovery', // Redacted to [REDACTED]
}, 'User action');

// Browser console output:
// { email: "[REDACTED]", message: "[REDACTED]", ... }
```

**Purpose:** Prevent PHI from appearing in:
- Browser DevTools console
- Sentry error reports (if logs sent to Sentry)
- Browser extensions (malicious extensions can't read PHI)

**Layer 2: Server-Side Redaction (Dave, Warp API routes)**

```python
# Dave/api/app/core/logging.py
logger.info("user_action", email="user@example.com", recovery_status="in_recovery")

# Cloud Logging output:
# { "email": "[REDACTED]", "recovery_status": "[REDACTED]", ... }
```

**Purpose:** Prevent PHI from being stored in:
- GCP Cloud Logging (6-year retention)
- Log archives (backup systems)
- Third-party log analytics (if integrated)

**Why both layers needed:**

**Scenario: Client-side redaction only**
- ❌ If Warp API route logs request payload, PHI stored in Cloud Logging
- ❌ Developers debug production logs, see unredacted PHI
- ❌ HIPAA violation (PHI stored without patient consent)

**Scenario: Server-side redaction only**
- ❌ If browser logs user input, PHI visible in DevTools
- ❌ Sentry captures unredacted logs, PHI sent to third party
- ❌ HIPAA violation (PHI transmitted to unauthorized party)

**Scenario: Both layers (defense in depth)**
- ✅ PHI redacted before browser console (client-side)
- ✅ PHI redacted before Cloud Logging (server-side)
- ✅ HIPAA compliant (no PHI in logs or third parties)

**PHI Fields to Redact:**

| Field | Example | Why PHI |
|-------|---------|---------|
| email | user@example.com | Personally identifiable |
| name | John Doe | Personally identifiable |
| phone | 555-123-4567 | Personally identifiable |
| recovery_status | in_recovery | Protected health information |
| sobriety_date | 2025-01-01 | Protected health information |
| message (chat) | "I relapsed yesterday" | Protected health information |
| resume_text | "...treatment center..." | May contain PHI |
| cover_letter | "...my recovery journey..." | May contain PHI |

**Redaction Pattern:**

```typescript
// Email: user@example.com → [REDACTED]
// Phone: 555-123-4567 → [REDACTED]
// Recovery terms: "in recovery" → [REDACTED]
// User ID: abc123 → SHA-256 hash (for correlation without revealing identity)
```

### Log Structure (Minimal Core Fields)

**Why minimal core fields:**

**Philosophy:** Start simple, add fields as debugging needs emerge (avoid over-engineering)

**Core Fields (Always Present):**

```typescript
interface LogEntry {
  timestamp: string;        // When did this happen?
  level: "info" | "warn" | "error" | "debug"; // How severe?
  service: string;          // Which service logged this?
  traceId: string;          // How to correlate across services?
  userId?: string;          // Which user (hashed)?
  message: string;          // What happened?
  context?: object;         // Additional details (optional)
}
```

**Why NOT include additional fields (yet):**

| Field | Why Deferred |
|-------|--------------|
| `sessionId` | Can be derived from `traceId` (one request = one trace = one session context) |
| `recovery_status` | PHI risk (not needed for debugging, only for analytics) |
| `feature_flags` | Add when feature flags implemented (Phase 3+) |
| `request_id` | Same as `traceId` (no need for duplicate) |
| `ip_address` | Privacy concern (not needed for debugging, can query from Cloud Run logs) |

**Context Field (Optional):**

```typescript
// Example: API request log
logger.info({
  traceId: 'abc123',
  userId: 'hash_xyz',
  message: 'API request completed',
  context: {
    method: 'POST',
    path: '/api/v1/chat',
    duration_ms: 250,
    status: 200,
  },
});
```

**Benefits:**
- ✅ Minimal overhead (5 required fields, 1 optional)
- ✅ Flexible (context field for feature-specific data)
- ✅ Queryable (all services have same core fields)

---

## Alternatives Considered

### Option 1: Winston (Warp) + Structlog (Dave) ❌

**Pros:**
- ✅ Winston has rich feature set (transports, formatters, query logs)
- ✅ Large ecosystem (winston-sentry, winston-daily-rotate-file)

**Cons:**
- ❌ Slower (20k logs/sec vs 100k logs/sec for Pino)
- ❌ Larger bundle size (45KB vs 15KB for Pino)
- ❌ Not JSON-first (requires configuration)

**Verdict:** Rejected due to performance and bundle size.

### Option 2: Pino (Warp) + Structlog (Dave) ✅ **CHOSEN**

**Pros:**
- ✅ Ultra-fast (100k+ logs/sec)
- ✅ JSON-first output (GCP Cloud Logging native)
- ✅ Smaller bundle size (15KB)
- ✅ Standard in Next.js ecosystem
- ✅ Aligns with backend JSON logging (Structlog)

**Cons:**
- ⚠️ Fewer features than Winston (simpler API)

**Verdict:** Best performance, best GCP integration, best Next.js fit.

### Option 3: Custom Logger (Build Our Own) ❌

**Pros:**
- ✅ Full control over implementation
- ✅ Tailored to Employa needs

**Cons:**
- ❌ Reinventing the wheel (Pino already does what we need)
- ❌ Maintenance burden (we maintain the logger)
- ❌ No ecosystem (no plugins, no community support)

**Verdict:** Rejected due to maintenance burden.

---

## Implementation

### Phase 1: Pino Logger Setup (Warp) - Week 4, Days 1-2

**Files to Replace:**

`Warp/src/lib/logger.ts` (replace lines 1-57):

```typescript
import pino from 'pino';
import { redactPHI } from './logger-redaction';

const isDev = process.env.NODE_ENV === 'development';
const isServer = typeof window === 'undefined';

// Pino logger configuration
const logger = pino({
  level: isDev ? 'debug' : 'info',

  // Browser configuration
  browser: {
    asObject: true,
    serialize: true,
  },

  // Base fields for all logs
  base: {
    service: 'warp-frontend',
    environment: process.env.NODE_ENV,
  },

  // Pretty print in development
  ...(isDev && isServer ? {
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'HH:MM:ss',
        ignore: 'pid,hostname',
      },
    },
  } : {}),

  // Redaction configuration
  redact: {
    paths: [
      'req.headers.authorization',
      'req.headers.cookie',
      'res.headers["set-cookie"]',
      '*.email',
      '*.phone',
      '*.recovery_status',
      '*.message',  // Chat messages
      '*.password',
      '*.token',
    ],
    censor: '[REDACTED]',
  },

  // Custom serializers
  serializers: {
    err: pino.stdSerializers.err,
    req: (req) => {
      return {
        method: req.method,
        url: redactPHI(req.url),  // Redact PHI in URL params
        headers: {
          'user-agent': req.headers['user-agent'],
        },
      };
    },
    res: (res) => {
      return {
        statusCode: res.statusCode,
      };
    },
  },
});

// Add trace ID to all logs (for correlation)
export function createLogger(traceId?: string) {
  if (traceId) {
    return logger.child({ traceId });
  }
  return logger;
}

export { logger };
export default logger;
```

**Files to Create:**

`Warp/src/lib/logger-redaction.ts`:

```typescript
// PHI field patterns to redact
const PHI_PATTERNS = [
  /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,  // Emails
  /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,  // Phone numbers
  /\b\d{3}-\d{2}-\d{4}\b/g,  // SSN
  /\b(in recovery|recovering|sober|sobriety|clean time|relapse|sponsor)\b/gi,  // Recovery terms
];

export function redactPHI(text: string): string {
  if (!text) return text;

  let redacted = text;

  for (const pattern of PHI_PATTERNS) {
    redacted = redacted.replace(pattern, '[REDACTED]');
  }

  return redacted;
}

export function redactObject<T extends Record<string, any>>(obj: T): T {
  const redacted: any = {};

  for (const [key, value] of Object.entries(obj)) {
    // Redact sensitive field names
    if (['email', 'phone', 'recovery_status', 'message', 'password'].includes(key)) {
      redacted[key] = '[REDACTED]';
    } else if (typeof value === 'string') {
      redacted[key] = redactPHI(value);
    } else if (typeof value === 'object' && value !== null) {
      redacted[key] = redactObject(value);
    } else {
      redacted[key] = value;
    }
  }

  return redacted;
}
```

**Files to Modify:**

`Warp/package.json`:

```json
{
  "dependencies": {
    "pino": "^8.17.0",
    "pino-pretty": "^10.3.0"
  }
}
```

### Phase 2: PHI Redaction (Dave) - Week 4, Days 2-3

**Files to Modify:**

`Dave/api/app/core/logging.py`:

```python
import re
import structlog
from typing import Any

# PHI patterns to redact
PHI_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
    (re.compile(r'\b(in recovery|recovering|sober|sobriety|clean time|relapse|sponsor)\b', re.IGNORECASE), '[RECOVERY]'),
]

# Sensitive field names to redact
SENSITIVE_FIELDS = {
    'email', 'phone', 'recovery_status', 'message', 'chat_history',
    'password', 'token', 'api_key', 'resume_text', 'cover_letter',
    'ssn', 'date_of_birth', 'address', 'sponsor_name', 'treatment_history'
}

def redact_phi(value: Any) -> Any:
    """Redact PHI from log values."""
    if isinstance(value, str):
        for pattern, replacement in PHI_PATTERNS:
            value = pattern.sub(replacement, value)
        return value
    elif isinstance(value, dict):
        return {k: '[REDACTED]' if k in SENSITIVE_FIELDS else redact_phi(v)
                for k, v in value.items()}
    elif isinstance(value, list):
        return [redact_phi(item) for item in value]
    else:
        return value

def add_phi_redaction(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Structlog processor to redact PHI from all log events."""
    # Redact all values in event dict
    for key in list(event_dict.keys()):
        if key in SENSITIVE_FIELDS:
            event_dict[key] = '[REDACTED]'
        else:
            event_dict[key] = redact_phi(event_dict[key])

    return event_dict

# Configure structlog with PHI redaction
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_phi_redaction,  # ADD THIS PROCESSOR
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

**Files to Create:**

`shared/employa-auth/employa_auth/logging.py` (shared redaction utility):

```python
"""Shared PHI redaction utilities for all Employa services."""
import re
from typing import Any

# Copy PHI_PATTERNS, SENSITIVE_FIELDS, redact_phi function from above

__all__ = ['redact_phi', 'PHI_PATTERNS', 'SENSITIVE_FIELDS']
```

### Phase 3: GCP Cloud Logging Integration - Week 4, Day 4

**Files to Create:**

`Dave/api/app/core/gcp_logging.py`:

```python
import json
import logging
import structlog
from google.cloud import logging as gcp_logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler

def setup_gcp_logging(service_name: str, environment: str):
    """
    Configure logging for GCP Cloud Logging.

    In production, sends logs to Cloud Logging.
    In development, logs to stdout.
    """
    if environment == "production":
        # Initialize GCP logging client
        client = gcp_logging.Client()
        handler = CloudLoggingHandler(client, name=service_name)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

        # Configure structlog to use GCP handler
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                add_phi_redaction,  # PHI redaction
                add_trace_context,  # Add trace ID for correlation
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development: pretty-printed logs to stdout
        structlog.configure(
            processors=[
                structlog.dev.set_exc_info,
                structlog.processors.add_log_level,
                structlog.dev.ConsoleRenderer(),
            ],
        )

def add_trace_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add GCP trace context for request correlation."""
    import contextvars
    trace_id = contextvars.ContextVar('trace_id', default=None).get()

    if trace_id:
        event_dict['logging.googleapis.com/trace'] = trace_id

    return event_dict
```

**Files to Modify:**

`Dave/api/app/main.py`:

```python
from app.core.gcp_logging import setup_gcp_logging
from app.config import settings

# Add after app initialization
setup_gcp_logging(service_name="dave-service", environment=settings.environment)
```

### Phase 4: Trace ID Correlation - Week 4, Day 5

**Files to Modify:**

`Warp/src/middleware.ts`:

```typescript
import { v4 as uuidv4 } from 'uuid';
import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

export function middleware(request: NextRequest) {
  // Generate trace ID for request correlation
  const traceId = uuidv4();

  // Log request with trace ID
  logger.info({
    traceId,
    method: request.method,
    url: request.nextUrl.pathname,
  }, 'Incoming request');

  // Add trace ID to response headers
  const response = NextResponse.next();
  response.headers.set('X-Trace-Id', traceId);

  return response;
}
```

**Files to Create:**

`Dave/api/app/middleware/correlation.py`:

```python
import contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

# Context var for trace ID (accessible in all request handlers)
trace_id_var = contextvars.ContextVar('trace_id', default=None)

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract trace ID from header (set by Warp or API Gateway)
        trace_id = request.headers.get('X-Trace-Id') or str(uuid.uuid4())

        # Set in context var for logging
        trace_id_var.set(trace_id)

        # Add to all log messages
        logger = structlog.get_logger().bind(traceId=trace_id)

        response = await call_next(request)
        response.headers['X-Trace-Id'] = trace_id

        return response
```

**Files to Modify:**

`Dave/api/app/main.py`:

```python
from app.middleware.correlation import CorrelationMiddleware

app.add_middleware(CorrelationMiddleware)
```

---

## Consequences

### Positive

1. **HIPAA Compliant:** PHI redacted before storage (defense in depth)
2. **Distributed Tracing:** `traceId` correlates logs across services
3. **Performance:** Pino is 5x faster than Winston (minimal overhead)
4. **GCP Native:** JSON logs ingested by Cloud Logging (no parsing)
5. **Minimal Overhead:** 5 core fields (not over-engineered)
6. **Audit Trail:** 6-year log retention (HIPAA requirement)

### Negative

1. **Migration Effort:** Replace `console.log()` with Pino (~200 instances in Warp)
2. **PHI Redaction Complexity:** Must maintain redaction patterns (email, phone, recovery terms)
3. **Testing:** Verify PHI redaction works (spot check 1000 log entries)

### Neutral

1. **Log Volume:** JSON logs larger than plaintext (but GCP compresses)
2. **Development Experience:** Pretty-printed logs in dev (human-readable)
3. **Production Logs:** JSON in Cloud Logging (query with filters)

---

## Success Metrics

### HIPAA Compliance Targets
- **Zero PHI leaks:** Spot check 1000 random log entries (0 PHI found)
- **Redaction coverage:** 100% of sensitive fields redacted
- **Audit retention:** 6-year log retention (Cloud Logging configured)

### Performance Targets
- **Log overhead:** <1ms per log statement (Pino performance)
- **Bundle size:** <20KB increase from Pino (negligible impact)

### Operational Targets
- **Trace correlation:** 100% of requests have `traceId` field
- **GCP integration:** 100% of logs ingested by Cloud Logging
- **Error Reporting:** 100% of errors create Error Reporting entries

### Testing Checklist
- [ ] Emails redacted as [REDACTED] in logs
- [ ] Phone numbers redacted as [REDACTED]
- [ ] Recovery terms redacted
- [ ] Logs have `traceId` for correlation
- [ ] GCP Cloud Logging shows structured JSON logs
- [ ] GCP Error Reporting captures errors with traces
- [ ] User ID hashed (SHA-256, not raw email)

---

## References

- **Phase 2 Epic:** [#328](https://github.com/employa-work/employa-web/issues/328)
- **Decision Plan:** `.claude/plans/snuggly-baking-hamster.md`
- **Pino Docs:** https://getpino.io/
- **Structlog Docs:** https://www.structlog.org/
- **GCP Cloud Logging:** https://cloud.google.com/logging/docs
- **HIPAA Logging Requirements:** https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html

---

## Notes

- **Current Warp Logger:** Custom utility at `Warp/src/lib/logger.ts` (replace with Pino)
- **Dave Logger:** Structlog already configured (add PHI redaction processor only)
- **Trace ID Format:** UUID v4 (generated by Warp middleware, propagated to services)
- **Log Retention:** GCP Cloud Logging default is 30 days (configure 6-year retention for HIPAA)
- **PHI Redaction Testing:** Manual spot check + automated tests (verify [REDACTED] appears)
- **Pino Pretty:** Used in development only (human-readable logs), JSON in production
