import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
  debug: false,

  // HIPAA Compliance: Strip PHI before sending to Sentry
  beforeSend(event) {
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

    // Remove request data
    if (event.request) {
      delete event.request.cookies;
      delete event.request.data;
      if (event.request.url) {
        event.request.url = stripQueryParams(event.request.url);
      }
      if (event.request.headers) {
        delete event.request.headers['authorization'];
        delete event.request.headers['cookie'];
      }
    }

    delete event.user;

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

    if (event.extra) {
      event.extra = redactObject(event.extra);
    }

    return event;
  },
});

function redactPHI(text: string): string {
  return text
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL_REDACTED]')
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE_REDACTED]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]')
    .replace(/(?:name|user|patient):\s*[^\s,]+(?:\s+[^\s,]+)*/gi, '$&[NAME_REDACTED]');
}

function stripQueryParams(url: string): string {
  try {
    const urlObj = new URL(url);
    return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
  } catch {
    return url.split('?')[0];
  }
}

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
