# DB Isolation and Migration Contracts

This standard defines database isolation, schema ownership, and migration contract requirements.

## DB Topology

- Per-service database instance from day one (no shared schemas)
- Shared instances are allowed only for legacy systems with an approved migration plan and end date

## Roles and Access

- One database role per service
- Least-privilege grants only
- No shared roles between services

## Migration Ownership

- Each service owns its migrations
- Migration contracts required for every change

## Legacy Migration Path (if shared instances exist)

- Create a dedicated database for the service before new feature work
- Use logical replication or dual-write only as a time-boxed migration step
- Cut over reads first, then writes, then decommission shared schema access
- Document the cutover plan and rollback in the service runbook

## Migration Contract Requirements

- SQL migration file(s)
- Backward-compatibility plan (expand/contract)
- API contract test updates
- Rollback plan
- **RLS policies** (see [database-rls-policies.md](database-rls-policies.md))
  - RLS MUST be enabled in the same migration as CREATE TABLE
  - All user-facing tables require RLS policies
  - Service role bypass policy required for backend operations
  - Automated RLS tests required (see [testing-rls-policies.md](testing-rls-policies.md))

## Access Patterns

- Cross-service access is API-only
- No direct DB access across services
