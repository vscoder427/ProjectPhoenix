/**
 * HIPAA-Compliant Logger with Allowlist-Based PHI Redaction
 *
 * Purpose: Ensure no PII/PHI is ever logged to external systems
 * Approach: Allowlist - only explicitly safe fields are logged, everything else redacted
 *
 * Safe Fields (exhaustive list):
 * - userId (UUID only, redacted to prevent re-identification)
 * - timestamp (ISO 8601 format)
 * - eventType (categorized event names)
 * - statusCode (HTTP status codes)
 * - errorCode (application error codes)
 * - component (component/module name)
 * - action (user action name)
 * - duration (timing in ms)
 * - count (numeric counts)
 *
 * NEVER log:
 * - email, name, phone, address
 * - Recovery details, milestones, notes
 * - Employer information
 * - Any user-generated content
 * - Session tokens, passwords, API keys
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: any;
}

interface SafeLogContext {
  userId?: string;
  timestamp?: string;
  eventType?: string;
  statusCode?: number;
  errorCode?: string;
  component?: string;
  action?: string;
  duration?: number;
  count?: number;
}

/**
 * Allowlist of safe fields that can be logged
 * Everything else is redacted
 */
const SAFE_FIELDS = new Set<keyof SafeLogContext>([
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

/**
 * Redacts all fields except those in the allowlist
 */
export function redactContext(context: LogContext): SafeLogContext {
  const safe: SafeLogContext = {};

  for (const [key, value] of Object.entries(context)) {
    if (SAFE_FIELDS.has(key as keyof SafeLogContext)) {
      // Additional redaction for userId - truncate to prevent re-identification
      if (key === 'userId' && typeof value === 'string') {
        safe.userId = `uuid-${value.slice(0, 8)}`;
      } else {
        (safe as any)[key] = value;
      }
    }
    // All other fields are silently dropped (not even logged as [REDACTED])
  }

  // Always add timestamp if not present
  if (!safe.timestamp) {
    safe.timestamp = new Date().toISOString();
  }

  return safe;
}

/**
 * Redacts PHI from error messages
 */
export function redactMessage(message: string): string {
  return message
    // Email addresses
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]')
    // Phone numbers (various formats)
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]')
    // SSN patterns
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]')
    // Credit card numbers (basic pattern)
    .replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[CC]')
    // Names (when preceded by common patterns)
    .replace(/\b(?:name|user|patient|client):\s*\S+(?:\s+\S+)*/gi, '[NAME]')
    // Addresses (basic pattern - number + street)
    .replace(/\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b/gi, '[ADDRESS]');
}

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development';

  /**
   * Log debug message (only in development)
   */
  debug(message: string, context?: LogContext) {
    if (this.isDevelopment) {
      this.log('debug', message, context);
    }
  }

  /**
   * Log info message
   */
  info(message: string, context?: LogContext) {
    this.log('info', message, context);
  }

  /**
   * Log warning
   */
  warn(message: string, context?: LogContext) {
    this.log('warn', message, context);
  }

  /**
   * Log error
   */
  error(message: string, context?: LogContext) {
    this.log('error', message, context);
  }

  /**
   * Core logging function with PHI redaction
   */
  private log(level: LogLevel, message: string, context?: LogContext) {
    const redactedMessage = redactMessage(message);
    const safeContext = context ? redactContext(context) : {};

    const logEntry = {
      level,
      message: redactedMessage,
      ...safeContext,
    };

    // Use appropriate console method
    const consoleFn = console[level] || console.log;
    consoleFn(JSON.stringify(logEntry));

    // In production, you could also send to external logging service
    // (e.g., GCP Cloud Logging, Datadog) after verifying no PHI in output
    if (!this.isDevelopment && typeof window === 'undefined') {
      // Server-side logging to external service
      // this.sendToCloudLogging(logEntry);
    }
  }

  /**
   * Log user action with automatic redaction
   * Use this for tracking user interactions
   */
  logUserAction(action: string, component: string, additionalContext?: LogContext) {
    this.info('User action', {
      action,
      component,
      eventType: 'user_action',
      ...additionalContext,
    });
  }

  /**
   * Log API call with automatic redaction
   */
  logApiCall(method: string, path: string, statusCode: number, duration: number) {
    // Strip query params from path
    const safePath = path.split('?')[0];

    this.info('API call', {
      eventType: 'api_call',
      component: `${method} ${safePath}`,
      statusCode,
      duration,
    });
  }

  /**
   * Log error with stack trace redaction
   */
  logError(error: Error, component?: string, additionalContext?: LogContext) {
    this.error(error.message, {
      component,
      errorCode: error.name,
      eventType: 'error',
      ...additionalContext,
    });
  }
}

// Export singleton instance
export const logger = new Logger();

// Export for testing
export { SAFE_FIELDS };
