# API Conventions

This standard defines the required API contract for all Employa microservices.

## Versioning

- **URL path versioning:** All endpoints under `/api/v1/`, `/api/v2/`, etc.
- Breaking changes require new major API version (e.g., v1 → v2)
- **30-day deprecation window:** Old versions deprecated for 30 days before sunset
- Maintain compatibility matrix in `docs/api-versions.md`

### Deprecation Headers (RFC 8594)

When an API version is deprecated, include these headers:

```
Deprecation: true
Sunset: Wed, 07 Feb 2026 00:00:00 GMT
Link: <https://docs.employa.work/migration>; rel="deprecation"
X-API-Deprecation-Days-Remaining: 15
```

### Migration Guides

- Required for all breaking changes
- Document what changed and how to migrate
- Include code examples for common use cases
- Publish before deprecation announcement

## Paths and Methods

- Use RESTful nouns, not verbs
- Use plural resource names: `/users`, `/meetings`, `/jobs`
- Use standard HTTP methods:
  - `GET` list or retrieve
  - `POST` create
  - `PUT` replace
  - `PATCH` partial update
  - `DELETE` remove

## Content Types

- Request and response `Content-Type` is `application/json`
- Reject non-JSON with `415 Unsupported Media Type`

## Request IDs

- Accept `X-Request-Id` from callers
- Generate one if absent
- Include `X-Request-Id` in all responses and logs

## Authentication

- Require auth on all endpoints unless explicitly public
- Standard header: `Authorization: Bearer <token>`
- Reject missing/invalid tokens with `401`

## Error Schema

All non-2xx responses must use this structure:

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human readable message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

## Pagination

- Use cursor or offset with a consistent response shape
- Response must include:
  - `items` (array)
  - `next_cursor` or `page`/`page_size`/`total`

## Filtering and Sorting

- Use query params for filters: `?status=active&city=baltimore`
- Use `sort` for ordering: `?sort=created_at:desc`

## Idempotency

- All write endpoints support idempotency
- Accept `Idempotency-Key` header for `POST`/`PUT`/`PATCH`

## Rate Limiting Headers

- Responses should include:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Deprecation

- Include `Deprecation` and `Sunset` headers for retiring endpoints
- Provide migration guide link in response headers or docs
