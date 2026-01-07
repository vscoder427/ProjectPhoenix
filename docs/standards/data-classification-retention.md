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

- Reference the [Data Classification Mapping](data-classification-mapping.md) standard when creating or updating classifications.

## Retention Policy

- PHI and PII retention must follow documented policy per service
- Retention periods must be justified and documented
- Legal hold supported for PHI/PII
- Retention and deletion must satisfy GDPR/CCPA requirements (see Privacy standard)

## Deletion Policy

- Deletion requests must be tracked and verified
- Deletion must cover primary data, backups, and derived artifacts
- Audit logs must record deletion events
- DSAR and "right to delete" requests must be handled within required timelines

## Logging Restrictions

- No PHI in logs
- PII redacted or masked in logs
- Logs follow retention policy by data class

## Data Inventory and Review

- Maintain a data inventory that links owners, classifications, retention timelines, and legal holds (see [Data Governance](data-governance.md)).
- Review inventory and retention policies annually or when business requirements change.
