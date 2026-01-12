import { redactContext, redactMessage, SAFE_FIELDS, logger } from './logger';

describe('Logger PHI Redaction', () => {
  describe('redactContext', () => {
    it('allows safe fields through', () => {
      const context = {
        userId: 'user-123-456-789',
        timestamp: '2026-01-12T12:00:00Z',
        eventType: 'profile_update',
        statusCode: 200,
        errorCode: 'VALIDATION_ERROR',
        component: 'ProfileForm',
        action: 'submit',
        duration: 150,
        count: 5,
      };

      const result = redactContext(context);

      expect(result.timestamp).toBe('2026-01-12T12:00:00Z');
      expect(result.eventType).toBe('profile_update');
      expect(result.statusCode).toBe(200);
      expect(result.errorCode).toBe('VALIDATION_ERROR');
      expect(result.component).toBe('ProfileForm');
      expect(result.action).toBe('submit');
      expect(result.duration).toBe(150);
      expect(result.count).toBe(5);
    });

    it('redacts userId to prevent re-identification', () => {
      const context = {
        userId: '12345678-1234-1234-1234-123456789012',
      };

      const result = redactContext(context);

      expect(result.userId).toBe('uuid-12345678');
      expect(result.userId).not.toContain('123456789012');
    });

    it('strips all non-safe fields', () => {
      const context = {
        email: 'user@example.com',
        name: 'John Doe',
        phone: '555-123-4567',
        address: '123 Main St',
        recoveryDate: '2025-01-01',
        employer: 'Acme Corp',
        notes: 'User notes here',
        customField: 'some value',
        statusCode: 200, // This is safe
      };

      const result = redactContext(context);

      // Safe field is kept
      expect(result.statusCode).toBe(200);

      // Unsafe fields are NOT present (not even as [REDACTED])
      expect(result).not.toHaveProperty('email');
      expect(result).not.toHaveProperty('name');
      expect(result).not.toHaveProperty('phone');
      expect(result).not.toHaveProperty('address');
      expect(result).not.toHaveProperty('recoveryDate');
      expect(result).not.toHaveProperty('employer');
      expect(result).not.toHaveProperty('notes');
      expect(result).not.toHaveProperty('customField');
    });

    it('adds timestamp if not present', () => {
      const context = {
        statusCode: 200,
      };

      const result = redactContext(context);

      expect(result.timestamp).toBeDefined();
      expect(typeof result.timestamp).toBe('string');
      expect(new Date(result.timestamp!).toISOString()).toBe(result.timestamp);
    });

    it('preserves existing timestamp', () => {
      const timestamp = '2026-01-01T00:00:00Z';
      const context = {
        timestamp,
        statusCode: 200,
      };

      const result = redactContext(context);

      expect(result.timestamp).toBe(timestamp);
    });
  });

  describe('redactMessage', () => {
    it('redacts email addresses', () => {
      const message = 'User email is john.doe@example.com';
      const result = redactMessage(message);

      expect(result).toBe('User email is [EMAIL]');
      expect(result).not.toContain('john.doe');
      expect(result).not.toContain('example.com');
    });

    it('redacts multiple email formats', () => {
      const message =
        'Emails: user@test.com, admin@domain.co.uk, test+tag@example.org';
      const result = redactMessage(message);

      expect(result).toBe('Emails: [EMAIL], [EMAIL], [EMAIL]');
    });

    it('redacts phone numbers in various formats', () => {
      const testCases = [
        { input: 'Call 555-123-4567', expected: 'Call [PHONE]' },
        { input: 'Phone: 555.123.4567', expected: 'Phone: [PHONE]' },
        { input: 'Contact: 5551234567', expected: 'Contact: [PHONE]' },
      ];

      testCases.forEach(({ input, expected }) => {
        expect(redactMessage(input)).toBe(expected);
      });
    });

    it('redacts SSN patterns', () => {
      const message = 'SSN: 123-45-6789';
      const result = redactMessage(message);

      expect(result).toBe('SSN: [SSN]');
      expect(result).not.toContain('123');
      expect(result).not.toContain('6789');
    });

    it('redacts credit card numbers', () => {
      const testCases = [
        { input: 'CC: 1234 5678 9012 3456', expected: 'CC: [CC]' },
        { input: 'Card: 1234-5678-9012-3456', expected: 'Card: [CC]' },
        { input: 'Number: 1234567890123456', expected: 'Number: [CC]' },
      ];

      testCases.forEach(({ input, expected }) => {
        expect(redactMessage(input)).toBe(expected);
      });
    });

    it('redacts names when preceded by common patterns', () => {
      const testCases = [
        { input: 'name: John Doe', expected: '[NAME]' },
        { input: 'user: jane_smith', expected: '[NAME]' },
        { input: 'patient: Robert', expected: '[NAME]' },
      ];

      testCases.forEach(({ input, expected }) => {
        expect(redactMessage(input)).toContain('[NAME]');
      });
    });

    it('redacts addresses', () => {
      const testCases = [
        '123 Main Street',
        '456 Oak Avenue',
        '789 Elm Road',
        '1000 Park Boulevard',
      ];

      testCases.forEach((address) => {
        const result = redactMessage(address);
        expect(result).toContain('[ADDRESS]');
      });
    });

    it('handles messages with multiple PHI types', () => {
      const message =
        'User john.doe@example.com (555-123-4567) lives at 123 Main Street. SSN: 123-45-6789';
      const result = redactMessage(message);

      expect(result).not.toContain('john.doe');
      expect(result).not.toContain('555-123-4567');
      expect(result).not.toContain('Main Street');
      expect(result).not.toContain('123-45-6789');
      expect(result).toContain('[EMAIL]');
      expect(result).toContain('[PHONE]');
      expect(result).toContain('[ADDRESS]');
      expect(result).toContain('[SSN]');
    });

    it('does not modify safe messages', () => {
      const message = 'User clicked submit button';
      const result = redactMessage(message);

      expect(result).toBe(message);
    });
  });

  describe('Logger methods', () => {
    let consoleInfoSpy: jest.SpyInstance;
    let consoleErrorSpy: jest.SpyInstance;
    let consoleLogSpy: jest.SpyInstance;

    beforeEach(() => {
      // Spy on all console methods that logger uses
      consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation();
      consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    });

    afterEach(() => {
      consoleInfoSpy.mockRestore();
      consoleErrorSpy.mockRestore();
      consoleLogSpy.mockRestore();
    });

    it('info logs with redacted context', () => {
      logger.info('User action', {
        userId: '12345678-1234-1234-1234-123456789012',
        email: 'user@example.com', // Should be stripped
        statusCode: 200,
      });

      expect(consoleInfoSpy).toHaveBeenCalledTimes(1);
      const logOutput = JSON.parse(consoleInfoSpy.mock.calls[0][0]);

      expect(logOutput.level).toBe('info');
      expect(logOutput.message).toBe('User action');
      expect(logOutput.userId).toBe('uuid-12345678');
      expect(logOutput.statusCode).toBe(200);
      expect(logOutput).not.toHaveProperty('email');
    });

    it('error logs with PHI redaction in message', () => {
      logger.error('Error processing email user@example.com', {
        statusCode: 500,
      });

      expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
      const logOutput = JSON.parse(consoleErrorSpy.mock.calls[0][0]);

      expect(logOutput.level).toBe('error');
      expect(logOutput.message).toBe('Error processing email [EMAIL]');
      expect(logOutput.message).not.toContain('user@example.com');
    });

    it('logUserAction creates properly structured log', () => {
      logger.logUserAction('click', 'SubmitButton', {
        duration: 150,
        name: 'John Doe', // Should be stripped
      });

      expect(consoleInfoSpy).toHaveBeenCalledTimes(1);
      const logOutput = JSON.parse(consoleInfoSpy.mock.calls[0][0]);

      expect(logOutput.action).toBe('click');
      expect(logOutput.component).toBe('SubmitButton');
      expect(logOutput.eventType).toBe('user_action');
      expect(logOutput.duration).toBe(150);
      expect(logOutput).not.toHaveProperty('name');
    });

    it('logApiCall redacts query params from path', () => {
      logger.logApiCall(
        'GET',
        '/api/users?email=user@example.com&name=John',
        200,
        50
      );

      expect(consoleInfoSpy).toHaveBeenCalledTimes(1);
      const logOutput = JSON.parse(consoleInfoSpy.mock.calls[0][0]);

      expect(logOutput.component).toBe('GET /api/users');
      expect(logOutput.component).not.toContain('email');
      expect(logOutput.component).not.toContain('name');
      expect(logOutput.statusCode).toBe(200);
      expect(logOutput.duration).toBe(50);
    });

    it('logError logs error without stack trace PHI', () => {
      const error = new Error('Failed to process email user@example.com');
      logger.logError(error, 'UserService', { statusCode: 500 });

      expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
      const logOutput = JSON.parse(consoleErrorSpy.mock.calls[0][0]);

      expect(logOutput.level).toBe('error');
      expect(logOutput.message).toBe('Failed to process email [EMAIL]');
      expect(logOutput.component).toBe('UserService');
      expect(logOutput.errorCode).toBe('Error');
      expect(logOutput.statusCode).toBe(500);
    });
  });

  describe('SAFE_FIELDS allowlist', () => {
    it('contains exactly the documented safe fields', () => {
      const expectedFields = new Set([
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

      expect(SAFE_FIELDS).toEqual(expectedFields);
    });

    it('does not contain any PII/PHI fields', () => {
      const unsafeFields = [
        'email',
        'name',
        'phone',
        'address',
        'ssn',
        'recoveryDate',
        'employer',
        'notes',
        'password',
        'token',
      ];

      unsafeFields.forEach((field) => {
        expect(SAFE_FIELDS.has(field as any)).toBe(false);
      });
    });
  });
});
