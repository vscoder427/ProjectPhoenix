# HIPAA Compliance Standard

This standard defines HIPAA requirements for systems that handle PHI. It applies to all Employa services and vendors that store, process, or transmit PHI.

## Administrative Safeguards

- Designate a HIPAA Security Owner
- Maintain a written risk analysis and risk management plan
- Define incident response and breach notification procedures
- Workforce training and access control policies

## Technical Safeguards

- Access control: least privilege and unique user identification
- Audit controls: log access to PHI and security events
- Integrity: tamper-evident logs and change tracking
- Transmission security: TLS for all data in transit
- Encryption at rest for all PHI data stores

## Physical Safeguards

- Vendor attestations for physical security controls
- Data center compliance verified via vendor reports

## Data Classification

- Classify data as PHI, PII, or non-sensitive
- PHI must be handled in HIPAA-compliant systems only
- Minimize PHI exposure and storage duration

## Minimum Necessary Standard

- Collect and store only the minimum PHI needed
- Mask or tokenize PHI where possible
- Restrict PHI access by role and service
-
- **Cross-reference:** follow the [Privacy (GDPR/CCPA) standard](privacy-gdpr-ccpa.md) for shared DSAR workflows when PHI overlaps with GDPR/CCPA.

## Vendor and BAA Requirements

- All vendors handling PHI must have a signed BAA
- Maintain a vendor BAA inventory and renewal schedule
- No PHI in systems without a BAA
-
> **Signal to agents:** Add risk analysis artifacts to the enterprise risk register and link to the privacy standard when PHI intersects with GDPR/CCPA jurisdictions.

## Monitoring and Auditing

- Centralized audit logging for all PHI access
- Regular access reviews and anomaly detection
- Retain audit logs per policy

## Breach Response

- Documented incident response plan with timelines
- Notification procedures aligned with HIPAA requirements
- Post-incident review and corrective actions

## Required Documentation

- Risk analysis report and updates
- Access control policy
- Data retention and deletion policy
- Vendor BAA inventory
