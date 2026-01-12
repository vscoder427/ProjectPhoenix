# ADR-0007: Role-Based Access Control (RBAC) & Admin Auth Consolidation

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#328](https://github.com/employa-work/employa-web/issues/328)
**Epic:** [#328](https://github.com/employa-work/employa-web/issues/328) - Phase 2 Foundation

---

## Context

Employa has **3 separate admin authentication implementations** across services:

1. **Warp Admin NextAuth JWT**: `verifyAdminAuth()` with 4-level role hierarchy (super_admin → admin → moderator → analyst)
2. **API-Level Admin API Key**: Single shared `ADMIN_API_KEY` environment variable used by Dave, CareerTools, AAMeetings
3. **CareerTools OAuth Link Token**: Special JWT link tokens for cross-service authentication

This fragmentation creates:
- **Security risk**: Single shared `ADMIN_API_KEY` is a single point of failure (no per-user audit trail)
- **Inconsistency**: Warp uses JWT with roles, services use shared key without roles
- **No audit trail**: Admin actions logged as "legacy-admin" instead of specific user
- **Scalability issues**: Cannot grant different permissions to different admins

Three key decisions needed:
1. **Admin Auth Consolidation**: How to unify the 3 implementations?
2. **Role Hierarchy**: What roles do we need (admin, employer, job seeker)?
3. **Enforcement Strategy**: Where to enforce RBAC (database, middleware, both)?

---

## Decision

**We will consolidate to unified JWT-based admin auth with defense-in-depth enforcement.**

### Admin Auth Consolidation
- **All admin access** uses JWT tokens from Warp login
- **Services validate JWT** using shared `employa_auth.jwt_validator` library
- **Admin role** checked via JWT claims (from Warp `users` table)
- **Retire** single shared `admin_api_key` (6-month deprecation timeline)
- **Audit logging** for all admin actions (who, what, when)

### Role Hierarchy

**Admin Roles (4 levels - keep current):**
- `super_admin` (Level 4): Full system access, user management, billing, security monitoring
- `admin` (Level 3): Service operations, content moderation, analytics, financial reports
- `moderator` (Level 2): Content review, limited user management, basic analytics
- `analyst` (Level 1): Read-only analytics, reporting, limited data export

**Employer Roles (Phase 3+):**
- `employer_admin`: Company account management, team management, billing, all job postings
- `employer_recruiter`: Post jobs, review applications only (no billing, no team management)

**Job Seeker Role (default):**
- `job_seeker`: Profile management, job applications, Dave chatbot access, recovery milestones

### RBAC Enforcement Strategy
- **Defense in depth**: Both RLS and middleware
- **Database RLS policies**: Enforce data access at row level (Supabase)
- **API middleware**: Enforce operation permissions and business logic (FastAPI dependencies)
- **Frontend guards**: Route protection based on session role (Next.js middleware)
- **Audit trail**: Log all permission checks in structured logs (Cloud Logging)

---

## Rationale

### Admin Auth Consolidation

**Why unified JWT-based admin auth:**

**1. Security Improvement**

| Current (Shared API Key) | New (JWT-based) |
|--------------------------|-----------------|
| Single shared secret | Per-user tokens |
| No user attribution | Know which admin performed action |
| No role granularity | 4-level role hierarchy |
| Rotates rarely (manual) | Rotates automatically (15-min expiry) |
| Exposed in env vars | Stored in httpOnly cookies |

**2. Audit Trail**

**Current logs:**
```
[INFO] Admin action: Created system prompt "test-prompt"
       Admin: legacy-admin (unknown user)
```

**New logs:**
```
[INFO] Admin action: Created system prompt "test-prompt"
       Admin: damien@employa.work (user_id: abc123, role: super_admin)
       Trace ID: xyz789
```

**3. Granular Permissions**

**Current:** Binary access (admin or not)
- `ADMIN_API_KEY` grants full admin access (no granularity)

**New:** Role-based access (4 admin levels)
- `super_admin`: Can delete users, manage billing, security monitoring
- `admin`: Can manage users, content, analytics (no billing, no security)
- `moderator`: Can moderate content, limited user management (no analytics)
- `analyst`: Can view analytics, export data (read-only, no user management)

**4. Compliance (HIPAA)**

HIPAA requires:
- **Access logging**: Who accessed PHI (user attribution)
- **Minimum necessary**: Least privilege access (role-based permissions)
- **Audit trail**: 6-year retention of access logs

Shared API key fails all three (no user attribution, no least privilege, no audit trail).

### Role Hierarchy Design

**Why keep current 4-level admin hierarchy:**

**1. Already Implemented in Warp**
- Warp has 4 admin levels in `Warp/src/lib/admin-auth.ts`
- Permission mappings already defined:
  - `super_admin`: manage_users, manage_admins, system_config, security_monitoring, financial_reports
  - `admin`: manage_users, content_management, analytics_full, financial_reports
  - `moderator`: content_management, manage_users_limited, analytics_basic
  - `analyst`: analytics_basic, export_data_limited

**2. Covers All Use Cases**
- **System operations** (super_admin): Database migrations, security config, billing
- **Service operations** (admin): User support, content approval, reporting
- **Content moderation** (moderator): Flag inappropriate job postings, ban users
- **Data analysis** (analyst): View metrics, generate reports (read-only)

**3. Separation of Concerns**
- Not all admins need billing access (security risk)
- Not all admins need user deletion powers (compliance risk)
- Not all admins need security monitoring (least privilege principle)

**Why add employer roles in Phase 3+:**

**1. Multi-User Employer Accounts**
- Large employers (e.g., HR departments) need team collaboration
- `employer_admin`: Manages team, billing, all company job postings
- `employer_recruiter`: Posts jobs, reviews applications (no billing, no team management)

**2. Billing Separation**
- Only `employer_admin` can update payment methods (compliance requirement)
- Recruiters cannot see billing info (reduces liability)

**Why `job_seeker` is default role:**

- MVP focus is job seekers in recovery (primary user type)
- Employers come in Phase 3+ (not critical for MVP)

### RBAC Enforcement Strategy

**Why defense in depth (RLS + middleware + frontend):**

**Layer 1: Frontend Guards (First Line of Defense)**
```typescript
// Warp/src/middleware.ts
if (request.nextUrl.pathname.startsWith('/admin')) {
  if (!token?.is_admin) {
    return NextResponse.redirect('/auth/signin?error=AdminRequired');
  }
}
```
**Purpose:** Block unauthorized users at UI level (fast, user-friendly)

**Layer 2: API Middleware (Second Line of Defense)**
```python
# Dave/api/app/middleware/auth.py
@router.post("/system-prompts")
async def create_system_prompt(
    auth: AuthContext = Depends(verify_jwt_admin)  # Validates JWT
):
    logger.info(f"Admin action by user {auth.user_id}")
    ...
```
**Purpose:** Validate JWT, check role claims, log admin actions

**Layer 3: Database RLS (Last Line of Defense)**
```sql
-- Dave/supabase/migrations/...
CREATE POLICY "Admins can manage system prompts"
ON system_prompts FOR ALL
USING (
  (auth.jwt() ->> 'is_admin')::boolean = true
  AND (auth.jwt() ->> 'user_role') IN ('admin', 'super_admin')
);
```
**Purpose:** Even if middleware is bypassed (security vulnerability), database prevents unauthorized data access

**Why all three layers:**
- **Frontend guard**: User experience (immediate feedback)
- **Middleware**: Business logic enforcement + audit logging
- **RLS**: Security backstop (defense against SQL injection, middleware bugs)

---

## Alternatives Considered

### Option 1: Keep Shared API Key ❌

**Pros:**
- ✅ No migration work (keep current implementation)
- ✅ Simple configuration (single env var)

**Cons:**
- ❌ Security risk (single point of failure)
- ❌ No user attribution (cannot trace admin actions)
- ❌ No role granularity (binary admin access)
- ❌ HIPAA non-compliant (no audit trail)
- ❌ Cannot revoke access per-user (must rotate shared key)

**Verdict:** Rejected due to security and compliance concerns.

### Option 2: Hybrid (JWT for users, API keys for services) ❌

**Pros:**
- ✅ User admins get JWT with roles (audit trail)
- ✅ Service-to-service keeps API keys (simpler)

**Cons:**
- ❌ Still maintains 2 separate auth patterns (complexity)
- ❌ Service API keys still shared (no per-service keys)
- ❌ Partial audit trail (user actions logged, service actions not)

**Verdict:** Rejected because it doesn't fully solve the problem.

### Option 3: Unified JWT-Based Admin Auth ✅ **CHOSEN**

**Pros:**
- ✅ Single auth pattern (JWT everywhere)
- ✅ Per-user audit trail (know who did what)
- ✅ Role-based permissions (4 admin levels)
- ✅ HIPAA compliant (access logging, least privilege)
- ✅ Automatic token rotation (15-min access tokens)
- ✅ Revoke access per-user (invalidate JWT, no key rotation)

**Cons:**
- ⚠️ Breaking change (6-month migration timeline)
- ⚠️ Migration effort (update Dave, CareerTools, AAMeetings)
- ⚠️ Services must validate JWT (add dependency on `employa_auth`)

**Verdict:** Best long-term solution (security, compliance, audit trail).

---

## Implementation

### Phase 1: Add JWT Admin Auth Support (Week 2, Days 4-5)

**Files to Modify:**

**1. Add role validation to shared auth library**
`shared/employa-auth/employa_auth/jwt_validator.py` (after line 238):

```python
def require_admin_role(required_roles: list[str] = ["admin", "super_admin"]):
    """
    Dependency factory for admin role-based access control.

    Example:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            claims: JWTClaims = Depends(require_admin_role(["super_admin"]))
        ):
            ...
    """
    async def _check_admin_role(
        claims: JWTClaims = Security(verify_jwt)
    ) -> JWTClaims:
        user_role = claims.raw_claims.get("user_role")
        is_admin = claims.raw_claims.get("is_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

        if required_roles and user_role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' insufficient. Requires: {required_roles}"
            )

        return claims

    return _check_admin_role
```

**2. Add role claims to Warp JWT**
`Warp/src/lib/auth.ts` (in jwt callback, around line 349):

```typescript
async jwt({ token, user, account, trigger }) {
  if (user) {
    token.id = user.id;
    token.is_admin = (user as any).is_admin ?? false;
    token.account_type = (user as any).account_type ?? "job_seeker";

    // ADD: Map account_type to role hierarchy
    token.user_role = mapAccountTypeToRole(
      (user as any).account_type,
      token.is_admin
    );
  }
  return token;
}

function mapAccountTypeToRole(accountType: string, isAdmin: boolean): string {
  if (isAdmin) {
    // TODO: Query Warp users table for actual admin role
    // For now, all admins are "admin" role
    return "admin";
  }

  switch (accountType) {
    case "employer":
      return "employer_admin";
    case "job_seeker":
    default:
      return "job_seeker";
  }
}
```

**3. Add JWT admin auth to Dave (with legacy fallback)**
`Dave/api/app/middleware/auth.py` (after line 198):

```python
async def verify_jwt_admin(
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> AuthContext:
    """
    Verify admin-level access via JWT token.

    Supports both legacy admin API key (during deprecation period)
    and new JWT-based admin auth.
    """
    if not bearer:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required.",
        )

    # Check if it's the legacy admin API key (deprecation period)
    if settings.admin_api_key and secrets.compare_digest(
        bearer.credentials, settings.admin_api_key
    ):
        logger.warning(
            "Admin API key authentication used - DEPRECATED. "
            "Migrate to JWT-based admin auth. "
            "Support ends 2026-07-12."
        )
        return AuthContext(
            api_key=bearer.credentials,
            is_admin=True,
            tier="admin",
        )

    # Try JWT validation
    from employa_auth.jwt_validator import require_admin_role

    claims = await require_admin_role(["admin", "super_admin"])(bearer)

    return AuthContext(
        api_key=None,
        is_admin=True,
        user_id=claims.user_id,
        user_type="admin",
        tier="admin",
    )

# Convenience dependency
RequireJWTAdmin = Depends(verify_jwt_admin)
```

### Phase 2: Migrate Admin Endpoints (Week 3, Days 3-5)

**Files to Modify:**

**1. Dave admin endpoints**
Replace `RequireAdmin` with `RequireJWTAdmin`:

```python
# Before
@router.post("/system-prompts", dependencies=[RequireAdmin])
async def create_system_prompt(prompt: SystemPromptCreate):
    ...

# After
@router.post("/system-prompts")
async def create_system_prompt(
    prompt: SystemPromptCreate,
    auth: AuthContext = RequireJWTAdmin,  # Now accepts JWT or legacy API key
):
    logger.info(f"Admin action by user {auth.user_id or 'legacy-admin'}")
    ...
```

**2. CareerTools admin endpoints** (same pattern)
**3. AAMeetings admin endpoints** (same pattern)

### Phase 3: Database RLS Updates (Week 3, Days 3-5)

**Files to Create:**

**Dave RLS migration:**
`Dave/supabase/migrations/20260120000000_add_admin_rls_jwt.sql`:

```sql
-- Add admin RLS policy that checks JWT claims
CREATE POLICY "Admins can manage all system prompts"
ON system_prompts
FOR ALL
USING (
  -- Check if user is admin from JWT claims
  (auth.jwt() ->> 'is_admin')::boolean = true
  AND
  (auth.jwt() ->> 'user_role') IN ('admin', 'super_admin', 'moderator')
);

-- Keep existing API key policy for backward compatibility (deprecation period)
-- Will be removed after 6-month sunset
CREATE POLICY "Admin API key can manage system prompts (DEPRECATED)"
ON system_prompts
FOR ALL
USING (
  current_setting('request.jwt.claim.admin_api_key', true) = 'true'
);
```

**Warp RLS migration:**
`Warp/supabase/migrations/20260120000000_add_admin_rls_jwt.sql`:

```sql
-- Similar pattern for Warp users table, jobs table, etc.
CREATE POLICY "Admins can manage all users"
ON users
FOR ALL
USING (
  (auth.jwt() ->> 'is_admin')::boolean = true
  AND
  (auth.jwt() ->> 'user_role') IN ('super_admin', 'admin')
);
```

### Phase 4: Frontend Route Guards (Week 3, Days 1-2)

**Files to Modify:**

`Warp/src/middleware.ts`:

```typescript
import { getToken } from "next-auth/jwt";

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request });

  // Admin route protection
  if (request.nextUrl.pathname.startsWith('/admin')) {
    if (!token?.is_admin) {
      return NextResponse.redirect(
        new URL('/auth/signin?error=AdminRequired', request.url)
      );
    }

    // Check specific admin roles for sensitive routes
    if (request.nextUrl.pathname.startsWith('/admin/users')) {
      const userRole = token.user_role as string;
      if (!['super_admin', 'admin'].includes(userRole)) {
        return NextResponse.redirect(
          new URL('/admin?error=InsufficientPermissions', request.url)
        );
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/dashboard/:path*'],
};
```

**Files to Create:**

`Warp/src/hooks/useAuthorization.ts`:

```typescript
import { useSession } from 'next-auth/react';

export function useAuthorization() {
  const { data: session } = useSession();

  const hasRole = (requiredRoles: string[]) => {
    if (!session?.user) return false;
    const userRole = (session.user as any).user_role;
    return requiredRoles.includes(userRole);
  };

  const isAdmin = () => {
    return (session?.user as any)?.is_admin ?? false;
  };

  const isSuperAdmin = () => {
    return (session?.user as any)?.user_role === 'super_admin';
  };

  return { hasRole, isAdmin, isSuperAdmin };
}
```

---

## Consequences

### Positive

1. **Security:** Per-user tokens (no shared secrets), automatic rotation (15-min expiry)
2. **Audit Trail:** Know which admin performed each action (HIPAA compliant)
3. **Granular Permissions:** 4-level role hierarchy (least privilege principle)
4. **Compliance:** Access logging, minimum necessary, audit retention (HIPAA Security Rule)
5. **Revocation:** Invalidate JWT per-user (no key rotation needed)
6. **Consistency:** Single auth pattern across all services (reduced complexity)

### Negative

1. **Breaking Change:** 6-month migration timeline (both auth methods supported)
2. **Migration Effort:** Update Dave, CareerTools, AAMeetings (~2-3 weeks)
3. **Testing Effort:** Test all admin endpoints with JWT (~1 week)
4. **Communication:** Email admins about migration (3 emails over 6 months)

### Neutral

1. **Role Hierarchy:** Keep current 4 admin levels (no changes to Warp)
2. **Employer Roles:** Deferred to Phase 3+ (not needed for MVP)
3. **Frontend Guards:** Already implemented in Warp (extend to all admin routes)

---

## Migration Strategy

### Timeline: 6 Months (2026-01-15 to 2026-07-15)

**Phase 1: Dual Support (Months 1-5)**
- Deploy JWT admin auth
- Keep legacy `ADMIN_API_KEY` working
- Add deprecation warnings to logs
- Monitor API key usage frequency
- Update admin documentation

**Phase 2: Force Migration (Month 6)**
- Week 1-2: Send email notifications to admins
- Week 3: Increase warning log level to ERROR
- Week 4: Disable admin API key in staging (test migration)

**Phase 3: Retirement (After 6 months)**
- Remove admin API key validation code
- Remove `ADMIN_API_KEY` from GCP Secret Manager
- Update RLS policies to remove API key policy

### Communication Plan

- **Month 1 (Jan 2026):** Release notes mention JWT admin auth (new feature)
- **Month 3 (Mar 2026):** Email to admins: "Admin API key deprecation in 4 months"
- **Month 5 (May 2026):** Email to admins: "Admin API key deprecation in 1 month - ACTION REQUIRED"
- **Month 6 (Jun 2026):** Email to admins: "Admin API key disabled, migrate to JWT"
- **Month 7 (Jul 2026):** Retirement complete

### Rollback Plan

- Keep `ADMIN_API_KEY` in GCP Secret Manager for 6 months after retirement
- Rollback script to re-enable API key validation if critical issues
- Monitor error rate: If >5% auth failures, rollback and investigate

---

## Success Metrics

### Security Targets
- **User Attribution:** 100% of admin actions have user_id in logs (not "legacy-admin")
- **Role Enforcement:** 0 unauthorized admin actions (caught by RLS)
- **Token Rotation:** 100% of admin tokens expire within 15 minutes

### Operational Targets
- **Migration Success Rate:** <5% auth failures during migration (rollback trigger)
- **API Key Usage:** 0 admin API key authentications by Month 6, Week 4
- **Audit Log Coverage:** 100% of admin endpoints log user_id, action, timestamp

### Compliance Targets (HIPAA)
- **Access Logging:** 6-year retention of admin action logs
- **Least Privilege:** 100% of admins have appropriate role (not all super_admin)
- **Audit Trail:** Query "who accessed this user's profile" (user_id in logs)

### Testing Checklist
- [ ] Admin login via Warp sets JWT with `is_admin=true, user_role=admin`
- [ ] Admin API request to Dave validates JWT (returns 201)
- [ ] Non-admin API request to Dave returns 403 Forbidden
- [ ] Moderator cannot access `/admin/users` (insufficient permissions)
- [ ] Admin action logs include `user_id`, not "legacy-admin"
- [ ] Legacy API key still works (deprecation period, logs warning)
- [ ] RLS policy blocks non-admin access (even if middleware bypassed)

---

## References

- **Phase 2 Epic:** [#328](https://github.com/employa-work/employa-web/issues/328)
- **Decision Plan:** `.claude/plans/snuggly-baking-hamster.md`
- **Warp Admin Auth:** `Warp/src/lib/admin-auth.ts`
- **Dave Auth Middleware:** `Dave/api/app/middleware/auth.py`
- **Shared Auth Library:** `employa-workspace-ops/shared/employa-auth/`
- **HIPAA Security Rule:** https://www.hhs.gov/hipaa/for-professionals/security/index.html
- **OWASP Access Control:** https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

---

## Notes

- **4-Level Hierarchy:** Already implemented in Warp, extends to all services
- **Employer Roles:** Deferred to Phase 3+ (multi-user employer accounts)
- **Job Seeker Role:** Default role (no special permissions needed for MVP)
- **RLS Migration:** Safe to deploy (backward compatible with legacy API key policy)
- **Audit Logging:** Structured logs with user_id, action, timestamp (Cloud Logging)
- **6-Month Timeline:** Industry standard deprecation period (time for admins to migrate)
