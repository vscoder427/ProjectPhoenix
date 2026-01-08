# API Lifecycle Governance

This standard defines API lifecycle management and compatibility.

## Lifecycle Policy

- APIs use semantic versioning (MAJOR.MINOR.PATCH)
- Services have independent versions
- Version stored in `api/app/__version__.py` (single source of truth)
- Breaking changes increment MAJOR version
- New features increment MINOR version
- Bug fixes increment PATCH version

## Version Visibility

Version exposed in:
- OpenAPI spec (`/docs`)
- Health endpoint (`/metadata`)
- Response headers (`X-API-Version`)
- Docker image tags (`service:X.Y.Z`)
- Git tags (`vX.Y.Z`)

## Client Compatibility

- Breaking changes require migration guides
- **Deprecation window: 30 days** (aggressive for fast iteration)
- Maintain compatibility matrix in `docs/api-versions.md`

## Deprecation Process

5-step process for breaking changes:

1. **Announce:** Mark version deprecated via `mark_deprecated()` function
2. **Headers:** All responses include RFC 8594 `Deprecation` and `Sunset` headers
3. **Monitor:** Log all usage of deprecated endpoints
4. **Sunset:** After 30 days, return `410 Gone`
5. **Remove:** After sunset, remove deprecated code

## Review

- API changes require design review before implementation
- Document new versions and migration guides in the release readiness checklist and service spec so users know the compatibility story during the next deploy

See [Versioning Strategy](./versioning-strategy.md) for implementation details.
