# Architecture Decision Records (ADR) Standard

This standard defines how architectural decisions are documented.

## When to Create an ADR

- Any change that affects architecture, security, data model, or service boundaries
- Any decision with long-term operational or cost impact

## ADR Format

- Title
- Status (Proposed, Accepted, Deprecated, Superseded)
- Context
- Decision
- Consequences
- Alternatives considered

## Storage

- Store ADRs in `docs/adr/` within each service repo
- Index ADRs in `docs/adr/README.md`

## Governance

- ADRs require review before acceptance
- Superseded ADRs must link to the replacing record
