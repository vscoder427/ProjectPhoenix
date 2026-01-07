# Error Codes Registry

This standard defines a shared error code registry for APIs.

## Format

- `SERVICE.DOMAIN.CODE` (e.g., `AAMEETINGS.AUTH.INVALID_TOKEN`)

## Requirements

- Codes must be documented in the service spec
- Use consistent HTTP status mapping
- Avoid leaking internal details
- When new codes are added, cite them in a Decision Record (Lite) and add the list to the release notes so consumers are aware.
