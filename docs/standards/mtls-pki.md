# mTLS and PKI Standard

This standard defines certificate management for service-to-service mTLS.

## Certificates

- Service identity certificates required
- Automated rotation policy required

## Cloud Run Implementation (Required)

- Use multi-container Cloud Run with an Envoy sidecar enforcing mTLS
- Certificates issued by a centralized SPIRE server (or equivalent SPIFFE-compatible CA)
- Each service has a unique SPIFFE ID mapped to its service account
- Envoy validates peer identities against the trust bundle before routing
- Certificate rotation happens automatically (max 24h lifetime)

## Trust

- Central trust store maintained
- Revocation process documented
