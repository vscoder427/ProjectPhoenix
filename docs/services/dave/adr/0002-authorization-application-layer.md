# ADR-0002: Application-Layer Authorization for Cloud SQL

**Status:** Accepted
**Date:** 2026-01-13
**Deciders:** Platform Team
**Related:** [database-rls-policies.md](../../../standards/database-rls-policies.md), [auth-jwt.md](../../../standards/security/auth-jwt.md)

## Context

Dave is being migrated from Supabase to GCP Cloud SQL as part of the greenfield rebuild. The existing RLS policies standard was designed for Supabase, which provides:

- `auth.uid()` - Built-in function returning authenticated user ID
- `authenticated`, `service_role`, `anon` - Built-in PostgreSQL roles
- Automatic RLS enforcement with Supabase client

Cloud SQL is raw PostgreSQL without these features. We need to decide how to enforce authorization in the new architecture.

## Decision

**Implement authorization at the application layer (FastAPI) rather than database layer (RLS).**

All authorization checks will be performed in the Dave API before database queries execute:

```python
# Example: Conversation ownership check in FastAPI
async def get_conversation(conversation_id: UUID, user: User = Depends(get_current_user)):
    conversation = await db.get_conversation(conversation_id)
    if conversation.user_id != user.id and not user.is_admin:
        raise HTTPException(403, "Access denied")
    return conversation
```

## Consequences

### Positive

1. **Simpler database schema** - No RLS policies, roles, or custom functions to maintain
2. **Faster queries** - No RLS policy evaluation overhead on every query
3. **Single source of truth** - Authorization logic lives in API code, not split between API and DB
4. **Easier testing** - Unit test authorization in Python, no need for multi-role DB test fixtures
5. **Connection pooling friendly** - No need to pass user context on every connection
6. **Faster development** - Less PostgreSQL expertise required for authorization changes

### Negative

1. **No defense in depth** - If API has authorization bug, database won't catch it
2. **Every query must check auth** - Developers must remember to add checks (mitigated by middleware/dependencies)
3. **Direct DB access is privileged** - Anyone with DB credentials has full access

### Mitigations

| Risk | Mitigation |
|------|------------|
| Missing auth checks | FastAPI dependency injection pattern (`Depends(verify_ownership)`) |
| Direct DB access | Cloud SQL private IP only, no public access |
| Credential exposure | Secrets in GCP Secret Manager, IAM-based access |
| Audit requirements | Structured logging with user_id on all operations |

## Alternatives Considered

### Option B: RLS in Cloud SQL

Implement RLS using `current_setting('app.user_id')`:

```sql
-- Set user context on each request
SET app.user_id = 'user-uuid-here';

-- RLS policy checks this setting
CREATE POLICY "select_own" ON ai_conversations
  FOR SELECT USING (user_id = current_setting('app.user_id')::uuid);
```

**Rejected because:**
- Adds complexity without immediate benefit (single API client)
- Connection pooling requires careful context management
- Supabase-style `auth.uid()` would need custom implementation
- Can be added later if multiple clients need direct DB access

### Option C: Hybrid Approach

RLS for read operations, application-layer for writes.

**Rejected because:**
- Inconsistent mental model
- Partial defense in depth is confusing
- Adds complexity of both approaches

## Decision Criteria

| Criteria | App-Layer (A) | RLS (B) | Hybrid (C) |
|----------|---------------|---------|------------|
| Simplicity | ++ | - | -- |
| Defense in depth | - | ++ | + |
| Query performance | ++ | + | + |
| Developer experience | ++ | - | - |
| HIPAA compliance | + | ++ | + |
| Greenfield velocity | ++ | - | - |

**Winner: Option A** - Simplicity and velocity for greenfield, with path to add RLS later if needed.

## Compliance Notes

### HIPAA Requirements Met

1. **Access Control (164.312(a)(1))** - FastAPI JWT validation + ownership checks
2. **Audit Controls (164.312(b))** - Structured logging with correlation IDs
3. **Transmission Security (164.312(e)(1))** - TLS required, private VPC
4. **Integrity (164.312(c)(1))** - Input validation in Pydantic models

### Future RLS Addition

If we later need RLS (e.g., multiple services accessing Dave DB directly), we can add it without schema changes:

1. Create `app.user_id` setting infrastructure
2. Add RLS policies to existing tables
3. Update connection pool to set user context
4. No data migration required

## Follow-ups

- [ ] Update [database-rls-policies.md](../../../standards/database-rls-policies.md) to clarify Supabase vs Cloud SQL guidance
- [ ] Document authorization patterns in Dave API code
- [ ] Add authorization middleware/dependencies to FastAPI template
- [ ] Create security testing checklist for API authorization
