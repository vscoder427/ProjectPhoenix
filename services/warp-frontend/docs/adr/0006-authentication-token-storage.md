# ADR-0006: Authentication & Token Storage

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#328](https://github.com/employa-work/employa-web/issues/328)
**Epic:** [#328](https://github.com/employa-work/employa-web/issues/328) - Phase 2 Foundation

---

## Context

Warp-frontend requires secure authentication for:
- Job seekers (primary user type for MVP)
- Future: Employers, admins
- HIPAA compliance requirements (PHI protection for recovery-focused users)

Current implementation (Warp) uses NextAuth.js with:
- Google OAuth + Email/Password providers
- JWT session tokens (30-day expiry)
- Optional 2FA (TOTP + backup codes)

**Security Concern:** Current implementation may store tokens in localStorage (XSS vulnerability). HIPAA compliance requires stronger token security.

Three key decisions needed:
1. **Authentication Providers:** Which sign-in methods for MVP?
2. **Token Storage:** Where to store JWT session tokens?
3. **Auth Library:** Keep NextAuth.js or switch to Supabase Auth?

---

## Decision

**We will keep NextAuth.js with httpOnly cookie storage for JWT tokens.**

### Authentication Providers (Unchanged)
- **Google OAuth** (social login)
- **Email/Password** (traditional auth)
- **Optional 2FA** (TOTP + backup codes)
- **Future:** Consider Magic Links in Phase 3 for passwordless option

### Token Storage (Breaking Change)
- **Migrate from localStorage to httpOnly cookies**
- **Short-lived access tokens:** 15 minutes
- **Long-lived refresh tokens:** 30 days
- **Cookie attributes:**
  - `httpOnly: true` (not accessible via JavaScript)
  - `secure: true` (HTTPS only in production)
  - `sameSite: 'lax'` (CSRF protection)

### Auth Library (Unchanged)
- **Keep NextAuth.js** (already implemented and working)

---

## Rationale

### Authentication Providers

**Why keep Google OAuth + Email/Password:**
- ✅ Already implemented and tested in Warp
- ✅ Job seekers can choose preferred method (social vs traditional)
- ✅ Optional 2FA available for high-security users
- ✅ No additional OAuth providers needed for MVP (LinkedIn, GitHub not critical)

**Why defer Magic Links to Phase 3:**
- Recovery-friendly (no password to remember)
- But requires implementation work (not in existing Warp code)
- Phase 2 focus is infrastructure, not new features

### Token Storage Migration

**Why httpOnly cookies over localStorage:**

**1. HIPAA Compliance**
- **XSS Protection:** httpOnly cookies cannot be accessed by JavaScript
- **PHI Security:** Tokens may contain user role, account type (recovery status indirectly)
- **OWASP Recommendation:** httpOnly cookies are best practice for JWT storage

**2. Security Comparison**

| Storage Method | XSS Risk | CSRF Risk | HIPAA Compliant |
|----------------|----------|-----------|-----------------|
| localStorage | **High** (tokens stolen by XSS) | Low | ❌ No |
| httpOnly cookies | **Low** (JS cannot access) | Medium (mitigated by sameSite) | ✅ Yes |

**3. Token Lifecycle Improvement**
- **Current:** Single 30-day JWT token (long-lived access token = higher risk)
- **New:** Split token model
  - Access token: 15 minutes (short-lived, used for API calls)
  - Refresh token: 30 days (long-lived, used to get new access token)
- If access token stolen via XSS, attacker has only 15-minute window

**4. Industry Standard**
- NextAuth.js default is httpOnly cookies (we align with framework defaults)
- Other recovery-focused apps use httpOnly cookies (BetterHelp, Talkspace)

### Auth Library Choice

**Why keep NextAuth.js:**

**1. Already Implemented**
- Warp uses NextAuth.js at `Warp/src/lib/auth.ts`
- Google OAuth configured (client ID/secret in env)
- Email/Password configured with Supabase backend
- 2FA implemented (TOTP + backup codes)

**2. Flexible OAuth Management**
- Easy to add new providers (LinkedIn, GitHub) in Phase 3
- Standardized OAuth flow (authorization code grant)
- Battle-tested with 50k+ GitHub stars

**3. Migration Cost**
- Switching to Supabase Auth would require:
  - Rewriting all auth code (~500 lines)
  - Reconfiguring OAuth providers
  - Migrating user sessions (downtime risk)
  - Testing all auth flows (login, logout, 2FA)
- Estimated effort: 2-3 weeks (delays Phase 2 timeline)

**Why not Supabase Auth:**
- ❌ Requires full rewrite of Warp auth
- ❌ Less flexible OAuth provider management
- ✅ Simpler for new projects (but we have existing NextAuth.js code)
- ✅ Native RLS integration (not critical for MVP)

---

## Alternatives Considered

### Option 1: Keep localStorage + NextAuth.js ❌

**Pros:**
- ✅ No migration work (keep current implementation)
- ✅ Simpler client-side code (direct localStorage access)

**Cons:**
- ❌ XSS vulnerability (tokens stolen by malicious scripts)
- ❌ HIPAA non-compliant (PHI exposure risk)
- ❌ Long-lived access tokens (30-day exposure window)
- ❌ Fails security review

**Verdict:** Rejected due to HIPAA compliance requirements.

### Option 2: httpOnly cookies + NextAuth.js ✅ **CHOSEN**

**Pros:**
- ✅ HIPAA compliant (XSS protection)
- ✅ NextAuth.js supports httpOnly cookies (simple config change)
- ✅ Short-lived access tokens (15-minute exposure window)
- ✅ CSRF protection (sameSite=Lax)
- ✅ Industry best practice

**Cons:**
- ⚠️ Breaking change (2-week migration timeline)
- ⚠️ Requires code refactor (remove localStorage reads)

**Verdict:** Best balance of security and implementation effort.

### Option 3: httpOnly cookies + Supabase Auth ❌

**Pros:**
- ✅ HIPAA compliant (XSS protection)
- ✅ Simpler integration with Supabase RLS
- ✅ Built-in magic links (passwordless auth)

**Cons:**
- ❌ Full rewrite of Warp auth (500+ lines)
- ❌ Reconfigure all OAuth providers (Google)
- ❌ 2-3 week delay to Phase 2 timeline
- ❌ Less flexible OAuth management

**Verdict:** Too much migration effort for Phase 2.

---

## Implementation

### Phase 1: Add httpOnly Cookie Support (Week 2, Days 1-3)

**Files to Modify:**
- `Warp/src/lib/auth.ts` (lines 422-433)

```typescript
// Current session config
session: {
  strategy: "jwt",
  maxAge: 7 * 24 * 60 * 60, // 7 days
},

// New session config
session: {
  strategy: "jwt",
  maxAge: 30 * 24 * 60 * 60, // 30 days (refresh token)
},
cookies: {
  sessionToken: {
    name: `__Secure-next-auth.session-token`,
    options: {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      secure: process.env.NODE_ENV === 'production',
      maxAge: 30 * 24 * 60 * 60, // 30 days
    },
  },
  callbackUrl: {
    name: `__Secure-next-auth.callback-url`,
    options: {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      secure: process.env.NODE_ENV === 'production',
    },
  },
  csrfToken: {
    name: `__Host-next-auth.csrf-token`,
    options: {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      secure: process.env.NODE_ENV === 'production',
    },
  },
},
```

**Files to Create:**
- `Warp/src/lib/auth-migration.ts` - Deprecation warnings

```typescript
export function checkDeprecatedTokenStorage() {
  if (typeof window !== 'undefined') {
    const hasOldTokens = localStorage.getItem('auth-token') ||
                         localStorage.getItem('session-token');
    if (hasOldTokens) {
      console.warn(
        '[DEPRECATION] localStorage token storage is deprecated. ' +
        'Tokens are now stored in httpOnly cookies. ' +
        'This warning will become an error on 2026-02-15.'
      );
      localStorage.removeItem('auth-token');
      localStorage.removeItem('session-token');
    }
  }
}
```

**Files to Modify:**
- `Warp/src/lib/api/client.ts` - Remove localStorage token reads

```typescript
// Remove this pattern (if it exists)
const token = localStorage.getItem('auth-token'); // DELETE

// Use NextAuth session instead
import { getSession } from 'next-auth/react';

async function makeAuthenticatedRequest(url: string) {
  const session = await getSession();
  return fetch(url, {
    headers: {
      'Authorization': `Bearer ${session?.accessToken}`,
    },
  });
}
```

### Phase 2: Monitor & Communicate (Week 2, Days 4-7)

- Monitor deprecation warning frequency in Cloud Logging
- Send user communication if localStorage usage detected
- Document migration in release notes

### Phase 3: Enforce httpOnly Cookies (Week 3, Days 1-2)

- Remove localStorage token access code
- Remove deprecation warnings
- Verify no localStorage token access in codebase

**Verification Commands:**
```bash
# Check for localStorage token access
npx grep -r "localStorage.*token" Warp/src --exclude-dir=node_modules

# Test authentication in dev
npm run dev
# Open browser DevTools > Application > Cookies
# Verify: __Secure-next-auth.session-token has httpOnly=true
```

---

## Consequences

### Positive

1. **HIPAA Compliant**: XSS protection for tokens containing user role/account type
2. **Security Best Practice**: Aligns with OWASP recommendations
3. **Short-Lived Access Tokens**: 15-minute exposure window (vs 30-day)
4. **CSRF Protection**: sameSite=Lax mitigates CSRF attacks
5. **Framework Default**: NextAuth.js recommends httpOnly cookies
6. **Industry Standard**: Used by recovery-focused apps (BetterHelp, Talkspace)

### Negative

1. **Breaking Change**: 2-week migration timeline
2. **Code Refactor**: Remove localStorage token reads (~200 lines)
3. **Testing Effort**: Test all auth flows (login, logout, 2FA, session refresh)
4. **User Impact**: Existing sessions invalidated (users must re-login)

### Neutral

1. **No Feature Changes**: Same auth providers (Google, Email/Password)
2. **Same Auth Library**: NextAuth.js (no rewrite needed)
3. **Same User Experience**: Login flow unchanged (cookie storage invisible to users)

---

## Migration Strategy

### Timeline: 2 Weeks

**Phase 1 (Week 2, Days 1-3): Add Support**
- Deploy httpOnly cookie configuration
- Add deprecation warnings for localStorage
- Both methods work simultaneously

**Phase 2 (Week 2, Days 4-7): Monitor & Communicate**
- Monitor deprecation warning frequency
- Send user communication (if localStorage usage detected)
- Document migration in release notes

**Phase 3 (Week 3, Days 1-2): Enforce**
- Remove localStorage token access code
- Remove deprecation warnings
- Deploy enforcement

### Rollback Plan

- Revert to localStorage if >5% auth failure rate
- Restore old `auth.ts` configuration
- Investigate issues before re-attempting

### Communication Plan

- **Week 2, Day 1:** Release notes mention httpOnly cookie migration
- **Week 2, Day 4:** Email to users: "Enhanced security - sessions may require re-login"
- **Week 3, Day 1:** Email to users: "Migration complete - please report any issues"

---

## Success Metrics

### Security Targets
- **XSS Protection:** Zero token thefts via XSS (measured by unauthorized access logs)
- **Token Expiry:** 100% of access tokens expire within 15 minutes
- **Cookie Attributes:** 100% of session cookies have `httpOnly=true, sameSite=lax, secure=true` (production)

### Operational Targets
- **Auth Failure Rate:** < 5% during migration (rollback trigger)
- **User Re-Login Rate:** < 100% (users with valid refresh tokens don't re-login)
- **Deprecation Warning Frequency:** 0 warnings by Week 3, Day 2

### Testing Checklist
- [ ] Login with email/password sets httpOnly cookie
- [ ] Login with Google OAuth sets httpOnly cookie
- [ ] Logout clears session cookie
- [ ] Access token expires after 15 minutes
- [ ] Refresh token refreshes access token automatically
- [ ] CSRF token validated on state-changing requests
- [ ] No localStorage tokens exist after migration

---

## References

- **Phase 2 Epic:** [#328](https://github.com/employa-work/employa-web/issues/328)
- **Decision Plan:** `.claude/plans/snuggly-baking-hamster.md`
- **NextAuth.js Cookie Docs:** https://next-auth.js.org/configuration/options#cookies
- **OWASP JWT Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- **HIPAA Security Rule:** https://www.hhs.gov/hipaa/for-professionals/security/index.html
- **Warp Auth Implementation:** `Warp/src/lib/auth.ts`

---

## Notes

- **2FA Support:** Unchanged (TOTP + backup codes still work)
- **OAuth Providers:** Unchanged (Google OAuth still works)
- **Magic Links:** Deferred to Phase 3 (not critical for MVP)
- **Supabase Auth Migration:** Can be revisited in Phase 4+ if RLS integration becomes critical
- **Token Refresh:** NextAuth.js handles refresh token flow automatically (no client-side code needed)
