# Logging Redaction Rules

This standard defines required redaction rules for logs.

## Redaction

- Never log PHI
- Mask PII (email, phone, address) where present
- Redact tokens, passwords, and secrets
- Align redaction rules with the [Privacy (GDPR/CCPA)](privacy-gdpr-ccpa.md) and [HIPAA Compliance](hipaa-compliance.md) standards, and document in the release readiness checklist whenever redaction policies change.

## Validation

- Log redaction verified in tests
