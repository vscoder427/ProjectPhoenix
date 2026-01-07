"""Utility to update cross-document links after reorganizing docs/standards."""

from pathlib import Path

MAPPING = {
    "docs/standards/auth-jwt.md": "docs/standards/security/auth-jwt.md",
    "docs/standards/security-secrets.md": "docs/standards/security/security-secrets.md",
    "docs/standards/secrets-access-policy.md": "docs/standards/security/secrets-access-policy.md",
    "docs/standards/mtls-pki.md": "docs/standards/security/mtls-pki.md",
    "docs/standards/api-gateway-networking.md": "docs/standards/security/api-gateway-networking.md",
    "docs/standards/service-communication.md": "docs/standards/security/service-communication.md",
    "docs/standards/logging-redaction.md": "docs/standards/security/logging-redaction.md",
    "docs/standards/hipaa-compliance.md": "docs/standards/compliance/hipaa-compliance.md",
    "docs/standards/hipaa-baa-readiness.md": "docs/standards/compliance/hipaa-baa-readiness.md",
    "docs/standards/hipaa-risk-analysis.md": "docs/standards/compliance/hipaa-risk-analysis.md",
    "docs/standards/privacy-gdpr-ccpa.md": "docs/standards/compliance/privacy-gdpr-ccpa.md",
    "docs/standards/compliance-audit-readiness.md": "docs/standards/compliance/compliance-audit-readiness.md",
    "docs/standards/security-review-checklist.md": "docs/standards/compliance/security-review-checklist.md",
    "docs/standards/threat-modeling.md": "docs/standards/compliance/threat-modeling.md",
    "docs/standards/data-classification-retention.md": "docs/standards/compliance/data-classification-retention.md",
    "docs/standards/data-classification-mapping.md": "docs/standards/compliance/data-classification-mapping.md",
    "docs/standards/data-encryption-kms.md": "docs/standards/compliance/data-encryption-kms.md",
    "docs/standards/data-governance.md": "docs/standards/compliance/data-governance.md",
    "docs/standards/vendor-management.md": "docs/standards/compliance/vendor-management.md",
    "docs/standards/supply-chain-sbom.md": "docs/standards/compliance/supply-chain-sbom.md",
    "docs/standards/build-provenance.md": "docs/standards/compliance/build-provenance.md",
    "docs/standards/business-continuity.md": "docs/standards/compliance/business-continuity.md",
    "docs/standards/release-readiness.md": "docs/standards/operations/release-readiness.md",
    "docs/standards/release-readiness-tracking.md": "docs/standards/operations/release-readiness-tracking.md",
    "docs/standards/release-changelog.md": "docs/standards/operations/release-changelog.md",
    "docs/standards/runbook-templates.md": "docs/standards/operations/runbook-templates.md",
    "docs/standards/runbooks-incident-response.md": "docs/standards/operations/runbooks-incident-response.md",
    "docs/standards/logging-observability.md": "docs/standards/operations/logging-observability.md",
    "docs/standards/observability-implementation.md": "docs/standards/operations/observability-implementation.md",
    "docs/standards/slo-alert-templates.md": "docs/standards/operations/slo-alert-templates.md",
    "docs/standards/cost-management.md": "docs/standards/operations/cost-management.md",
    "docs/standards/background-jobs.md": "docs/standards/operations/background-jobs.md",
    "docs/standards/caching.md": "docs/standards/operations/caching.md",
}


def main():
    for path in Path("docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        modified = text
        for old, new in MAPPING.items():
            modified = modified.replace(old, new)
        if modified != text:
            path.write_text(modified, encoding="utf-8")


if __name__ == "__main__":
    main()
