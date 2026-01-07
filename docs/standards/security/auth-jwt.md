# Auth and JWT Standard

This standard defines authentication and token requirements for all services.

## Token Type

- Short-lived JWT access tokens
- Opaque refresh tokens

## Token Validation

- Gateway validation required
- Service middleware validation required
- Per-request policy engine enforced

## Claims

- Standard claims plus roles, scopes, and tenant

## Key Management

- Rotating keys with JWKS
- Rotation policy and audit logs required

## Session Handling

- Stateless auth with revocation list
- Anomaly detection for token misuse
