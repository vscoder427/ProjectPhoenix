import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring.
  // Adjust this value in production to reduce costs
  tracesSampleRate: 1.0,

  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,

  replaysOnErrorSampleRate: 1.0,

  // This sets the sample rate to be 10%. You may want this to be 100% while
  // in development and sample at a lower rate in production
  replaysSessionSampleRate: 0.1,

  // You can remove this option if you're not planning to use the Sentry Session Replay feature:
  integrations: [
    Sentry.replayIntegration({
      // Additional Replay configuration goes in here, for example:
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  // HIPAA Compliance: Strip PHI before sending to Sentry
  beforeSend(event, hint) {
    // Remove PII/PHI from error messages
    if (event.message) {
      event.message = redactPHI(event.message);
    }

    // Remove PII/PHI from exception values
    if (event.exception?.values) {
      event.exception.values = event.exception.values.map((exception) => {
        if (exception.value) {
          exception.value = redactPHI(exception.value);
        }
        return exception;
      });
    }

    // Remove request data that might contain PHI
    if (event.request) {
      delete event.request.cookies;
      delete event.request.data;

      // Strip query params from URL that might contain PII
      if (event.request.url) {
        event.request.url = stripQueryParams(event.request.url);
      }

      // Remove sensitive headers
      if (event.request.headers) {
        delete event.request.headers['authorization'];
        delete event.request.headers['cookie'];
      }
    }

    // Remove user context (might contain email, name)
    delete event.user;

    // Redact breadcrumbs that might contain PHI
    if (event.breadcrumbs) {
      event.breadcrumbs = event.breadcrumbs.map((breadcrumb) => {
        if (breadcrumb.message) {
          breadcrumb.message = redactPHI(breadcrumb.message);
        }
        if (breadcrumb.data) {
          breadcrumb.data = redactObject(breadcrumb.data);
        }
        return breadcrumb;
      });
    }

    // Redact extra context
    if (event.extra) {
      event.extra = redactObject(event.extra);
    }

    return event;
  },

  // Performance monitoring
  beforeSendTransaction(event) {
    // Strip query params from transaction names
    if (event.transaction) {
      event.transaction = stripQueryParams(event.transaction);
    }
    return event;
  },
});

/**
 * Redacts PHI from strings using pattern matching
 * HIPAA-safe patterns: email, phone, SSN patterns
 */
function redactPHI(text: string): string {
  return text
    // Email addresses
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL_REDACTED]')
    // Phone numbers (various formats)
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE_REDACTED]')
    // SSN patterns
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]')
    // Names (when followed by common patterns like "Name:", "User:")
    .replace(/(?:name|user|patient):\s*[^\s,]+(?:\s+[^\s,]+)*/gi, '$&[NAME_REDACTED]');
}

/**
 * Strips query parameters from URLs
 */
function stripQueryParams(url: string): string {
  try {
    const urlObj = new URL(url);
    return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
  } catch {
    // If URL parsing fails, try basic string manipulation
    return url.split('?')[0];
  }
}

/**
 * Allowlist approach: only keep safe fields
 * Everything else is redacted
 */
const SAFE_FIELDS = new Set([
  'userId',
  'timestamp',
  'eventType',
  'statusCode',
  'errorCode',
  'component',
  'action',
  'duration',
  'count',
]);

function redactObject(obj: any): any {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  const redacted: any = {};
  for (const [key, value] of Object.entries(obj)) {
    if (SAFE_FIELDS.has(key)) {
      redacted[key] = value;
    } else {
      redacted[key] = '[REDACTED]';
    }
  }
  return redacted;
}
