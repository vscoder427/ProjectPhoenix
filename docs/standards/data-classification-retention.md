# Data Classification and Retention Standard

This standard defines how data is classified, stored, retained, and deleted across Employa services.

## Data Classes

- PHI: Protected health information
- PII: Personally identifiable information
- Internal: Non-public business data
- Public: Public or non-sensitive data

## Handling Requirements

- PHI: HIPAA-compliant storage only, encrypted in transit and at rest
- PII: Encrypted in transit and at rest, access controlled
- Internal: Access controlled, logged
- Public: No special handling requirements

## Retention Policy

- PHI and PII retention must follow documented policy per service
- Retention periods must be justified and documented
- Legal hold supported for PHI/PII

## Deletion Policy

- Deletion requests must be tracked and verified
- Deletion must cover primary data, backups, and derived artifacts
- Audit logs must record deletion events

## Logging Restrictions

- No PHI in logs
- PII redacted or masked in logs
- Logs follow retention policy by data class
