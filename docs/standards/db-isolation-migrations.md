# DB Isolation and Migration Contracts

This standard defines database isolation, schema ownership, and migration contract requirements.

## DB Topology

- Single Postgres instance with per-service schemas

## Roles and Access

- One database role per service
- Least-privilege grants only
- No shared roles between services

## Migration Ownership

- Each service owns its migrations
- Migration contracts required for every change

## Migration Contract Requirements

- SQL migration file(s)
- Backward-compatibility plan (expand/contract)
- API contract test updates
- Rollback plan

## Access Patterns

- Cross-service access is API-only
- No direct DB access across services
