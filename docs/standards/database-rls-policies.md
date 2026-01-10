# Row Level Security (RLS) Policies Standard

**Status:** Active
**Version:** 1.0
**Last Updated:** 2026-01-09
**Applies To:** All Employa services with database access
**Tier Requirement:** Mandatory for Tier 0 (HIPAA-compliant), Tier 1, Tier 2

---

## Overview

Row Level Security (RLS) is PostgreSQL's mechanism for restricting which rows users can access in database queries. For HIPAA-compliant multi-tenant systems like Employa, RLS is the **last line of defense** protecting sensitive user data.

This standard defines required RLS patterns, naming conventions, testing requirements, and common pitfalls to ensure consistent, secure database access across all Employa services.

---

## Why RLS Matters

### HIPAA Compliance
- **PHI Protection:** Prevents accidental exposure of Protected Health Information across tenant boundaries
- **Defense in Depth:** Complements API-level authorization (users can't bypass auth to access DB directly)
- **Audit Requirement:** RLS policies are logged and auditable for compliance reviews

### Multi-Tenant Security
- **Data Isolation:** Users can only access their own data by default
- **Fail Secure:** Database denies access unless explicitly allowed by policy
- **Service Isolation:** Backend services use `service_role` to bypass RLS when needed

### Historical Context
In 2026-01-05, **69 Employa tables** were found without RLS enabled, requiring emergency bulk migration ([20260105000001_enable_rls_all_tables.sql](../../Warp/supabase/migrations/20260105000001_enable_rls_all_tables.sql)). This standard prevents recurrence.

---

## Core Principles

### 1. Defense in Depth
RLS is the **last line of defense**, not a replacement for API-level authorization.

```
┌─────────────────────────────────────────────┐
│  Client (Next.js, Mobile App)              │
│  ✓ JWT authentication required             │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│  API Layer (FastAPI, Next.js API Routes)   │
│  ✓ JWT validation                           │
│  ✓ Role-based access control (RBAC)        │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│  Database (Supabase/PostgreSQL)             │
│  ✓ RLS policies enforce tenant isolation   │  ← Last line of defense
│  ✓ Service role bypasses RLS               │
└─────────────────────────────────────────────┘
```

### 2. Least Privilege
Grant **minimum necessary access**:
- Users: Access only their own data
- Authenticated users: Read public data (jobs, FAQs)
- Admins: Access based on role check
- Service role: Full access (backend services only)

### 3. Service Isolation
Backend services use `service_role` key to bypass RLS for:
- Bulk operations (data migrations, cleanup jobs)
- Cross-tenant admin operations
- Trigger functions requiring elevated privileges

### 4. Fail Secure
- **Default deny:** No RLS policy = no access
- **Explicit allow:** Policies must explicitly grant SELECT, INSERT, UPDATE, DELETE
- **Never skip RLS:** Service role is the only bypass mechanism

---

## Standard Policy Templates

### Template 1: User-Owned Resource

**Use Case:** User-owned data (profiles, conversations, applications, resumes)
**Frequency:** ~90% of tables

```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profiles
CREATE POLICY "select_own_user_profiles"
  ON user_profiles
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Users can insert their own profiles
CREATE POLICY "insert_own_user_profiles"
  ON user_profiles
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own profiles
CREATE POLICY "update_own_user_profiles"
  ON user_profiles
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Users can delete their own profiles
CREATE POLICY "delete_own_user_profiles"
  ON user_profiles
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Service role bypasses RLS (for backend operations)
CREATE POLICY "service_role_user_profiles"
  ON user_profiles
  FOR ALL
  TO service_role
  USING (true);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON user_profiles TO authenticated;
GRANT ALL ON user_profiles TO service_role;
```

**Key Features:**
- ✅ Separate policy per operation (SELECT, INSERT, UPDATE, DELETE)
- ✅ `WITH CHECK` clause for INSERT/UPDATE (prevents users from creating records they can't access)
- ✅ Service role bypass for backend services
- ✅ Explicit permission grants

---

### Template 2: Child Resource (Via Parent Join)

**Use Case:** Child tables without direct `user_id` (messages in conversations, skills in assessments)
**Frequency:** ~30% of tables

```sql
ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;

-- Users can view messages in their own conversations
CREATE POLICY "select_own_ai_messages"
  ON ai_messages
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM ai_conversations
      WHERE ai_conversations.id = ai_messages.conversation_id
        AND ai_conversations.user_id = auth.uid()
    )
  );

-- Users can insert messages in their own conversations
CREATE POLICY "insert_own_ai_messages"
  ON ai_messages
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM ai_conversations
      WHERE ai_conversations.id = ai_messages.conversation_id
        AND ai_conversations.user_id = auth.uid()
    )
  );

-- UPDATE and DELETE follow same pattern

-- Service role bypass
CREATE POLICY "service_role_ai_messages"
  ON ai_messages
  FOR ALL
  TO service_role
  USING (true);

GRANT SELECT, INSERT, UPDATE, DELETE ON ai_messages TO authenticated;
GRANT ALL ON ai_messages TO service_role;
```

**Key Features:**
- ✅ `EXISTS` subquery enforces transitive ownership (parent → child)
- ✅ Same policy logic for USING and WITH CHECK
- ⚠️ **Warning:** Ensure parent table (`ai_conversations`) has RLS enabled to prevent infinite recursion

---

### Template 3: Public Read, Owner Write

**Use Case:** Content that needs public discovery (jobs, companies, knowledge base articles)
**Frequency:** ~15% of tables

```sql
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Anyone (including anonymous) can view published jobs
CREATE POLICY "public_read_jobs"
  ON jobs
  FOR SELECT
  USING (
    status = 'active'
    AND published_at <= NOW()
  );

-- Employers can manage their own jobs
CREATE POLICY "employer_manage_jobs"
  ON jobs
  FOR ALL
  TO authenticated
  USING (employer_id = auth.uid())
  WITH CHECK (employer_id = auth.uid());

-- Service role has full access
CREATE POLICY "service_role_jobs"
  ON jobs
  FOR ALL
  TO service_role
  USING (true);

-- Grant permissions
GRANT SELECT ON jobs TO anon, authenticated;  -- Public read
GRANT INSERT, UPDATE, DELETE ON jobs TO authenticated;  -- Owner write
GRANT ALL ON jobs TO service_role;
```

**Key Features:**
- ✅ Public SELECT policy with conditions (status, timestamp filters)
- ✅ Separate owner-based write policy
- ✅ Prevents future-dated jobs from being visible (published_at filter)
- ⚠️ **Warning:** Never use `USING (true)` without conditions for public policies

---

### Template 4: Admin-Only Resource

**Use Case:** Configuration tables (nudge_rules, email_templates, admin_settings)
**Frequency:** ~10% of tables

```sql
-- Helper function (create once, reuse for all admin tables)
CREATE OR REPLACE FUNCTION is_admin_user()
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER  -- Run with elevated privileges
SET search_path = public  -- Prevent schema injection attacks
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
      AND (account_type = 'admin' OR is_admin = true)
  );
END;
$$;

-- Table RLS
ALTER TABLE admin_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin_only_admin_settings"
  ON admin_settings
  FOR ALL
  TO authenticated
  USING (is_admin_user());

CREATE POLICY "service_role_admin_settings"
  ON admin_settings
  FOR ALL
  TO service_role
  USING (true);

GRANT ALL ON admin_settings TO authenticated;
GRANT ALL ON admin_settings TO service_role;
```

**Key Features:**
- ✅ `SECURITY DEFINER` function allows policy to query `users` table
- ✅ `SET search_path = public` prevents SQL injection via schema attacks
- ✅ Reusable `is_admin_user()` function across multiple tables
- ✅ Single policy for all operations (admins get full access)

---

### Template 5: Service-Only Resource

**Use Case:** Internal tables (analytics_events, system_logs, email_tracking, audit_trails)
**Frequency:** ~20% of tables

```sql
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Only service role can access (no user access)
CREATE POLICY "service_only_analytics_events"
  ON analytics_events
  FOR ALL
  TO service_role
  USING (true);

-- No permissions for authenticated or anon users
GRANT ALL ON analytics_events TO service_role;
```

**Key Features:**
- ✅ Single policy: service role only
- ✅ No user-facing access at all
- ✅ Used for backend-only tables (logs, metrics, internal state)

---

## Naming Convention

### Standard Format
```
{operation}_{scope}_{table_name}
```

### Operation Prefixes
- `select_` - SELECT operations
- `insert_` - INSERT operations
- `update_` - UPDATE operations
- `delete_` - DELETE operations
- `manage_` - All operations (used when USING logic is identical)

### Scope Keywords
- `own_` - User owns the resource (`auth.uid() = user_id`)
- `public_` - Anyone can access (including anonymous)
- `admin_` - Admin role required
- `service_` - Service role only
- `role_` - Custom role-based access

### Examples
```sql
-- Good naming (follows standard)
"select_own_user_profiles"
"insert_own_ai_conversations"
"public_read_jobs"
"admin_only_notification_templates"
"service_role_analytics_events"

-- Old style (deprecated but acceptable for legacy tables)
"Users can view their own profiles"
"Anyone can view published jobs"
"Service role full access to users"
```

**Migration Note:** New tables MUST use standard naming. Legacy tables can keep old naming but should be updated during major schema refactors.

---

## Service Role Pattern

### Universal Bypass

**Every RLS-enabled table** must have a service role bypass policy:

```sql
CREATE POLICY "service_role_{table_name}"
  ON {table_name}
  FOR ALL
  TO service_role
  USING (true);
```

### Use Cases
1. **Backend Services:** Dave, AAMeetings, Outreach APIs need full database access
2. **Migrations:** Data migrations bypass user-level restrictions
3. **Trigger Functions:** Auto-creating related records on user signup
4. **Admin Tools:** Internal dashboards, reporting, bulk operations

### Security Considerations

**Service role key (`SUPABASE_SERVICE_KEY`) must:**
- ✅ Be stored in GCP Secret Manager (never in git)
- ✅ Only be accessible to authorized services
- ✅ Be rotated regularly (quarterly minimum)
- ✅ Never be used in client-side code

**Environment Variables:**
```bash
# Backend services (Dave, AAMeetings, Outreach)
DAVE_SUPABASE_SERVICE_KEY=<service-role-key>

# Frontend (Next.js) - NEVER use service key client-side
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>  # Safe for client-side
```

---

## Security Checklist

Before deploying any table with RLS:

- [ ] **RLS enabled** on all tables with user data (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)
- [ ] **Policies defined** for all operations user needs (SELECT, INSERT, UPDATE, DELETE)
- [ ] **WITH CHECK clause** included for UPDATE/INSERT policies (prevents policy violations)
- [ ] **Service role bypass** policy exists for backend operations
- [ ] **No overly broad policies** (`USING (true)` only for service role or with strong conditions)
- [ ] **Consistent user_id type** (UUID preferred over TEXT)
- [ ] **SECURITY DEFINER functions** use `SET search_path = public` (prevents injection)
- [ ] **Public policies** include status/timestamp filters (no unrestricted public access)
- [ ] **Grant statements** match policy permissions (e.g., `GRANT SELECT` if SELECT policy exists)

---

## Common Pitfalls

### Pitfall 1: Missing RLS on New Tables

**Problem:** 69 Employa tables were initially created without RLS ([Issue #20260105000001](../../Warp/supabase/migrations/20260105000001_enable_rls_all_tables.sql))

**Bad Example:**
```sql
-- Migration: 20260108_user_documents.sql
CREATE TABLE user_documents (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  content TEXT
);
-- ❌ RLS not enabled - SECURITY VULNERABILITY
```

**Good Example:**
```sql
-- Migration: 20260108_user_documents.sql
CREATE TABLE user_documents (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ✅ Enable RLS in same migration
ALTER TABLE user_documents ENABLE ROW LEVEL SECURITY;

-- ✅ Apply policies immediately
CREATE POLICY "select_own_user_documents" ON user_documents
  FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "service_role_user_documents" ON user_documents
  FOR ALL TO service_role USING (true);

GRANT SELECT ON user_documents TO authenticated;
GRANT ALL ON user_documents TO service_role;
```

**Fix:** Always enable RLS in the **same migration** as `CREATE TABLE`.

---

### Pitfall 2: Recursive Policy Issues

**Problem:** Jobs table joins employer_profiles, but employer_profiles had no policy allowing anonymous SELECT, causing "infinite recursion detected" errors.

**Bad Example:**
```sql
-- employer_profiles table
ALTER TABLE employer_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "owner_manage_employer_profiles" ON employer_profiles
  FOR ALL TO authenticated USING (user_id = auth.uid());
-- ❌ No public read policy

-- jobs table (tries to join employer_profiles)
CREATE POLICY "public_read_jobs" ON jobs
  FOR SELECT USING (
    status = 'active'
    AND EXISTS (SELECT 1 FROM employer_profiles WHERE employer_profiles.id = jobs.employer_id)
  );
-- ❌ Fails: anonymous users can't read employer_profiles
```

**Good Example:**
```sql
-- employer_profiles table
ALTER TABLE employer_profiles ENABLE ROW LEVEL SECURITY;

-- ✅ Allow public read (company profiles are discoverable)
CREATE POLICY "public_read_employer_profiles" ON employer_profiles
  FOR SELECT USING (true);

CREATE POLICY "owner_manage_employer_profiles" ON employer_profiles
  FOR ALL TO authenticated USING (user_id = auth.uid());
```

**Fix:** Ensure all joined tables have appropriate public read policies when needed.

---

### Pitfall 3: Inconsistent user_id Types

**Problem:** Some tables use `UUID`, others use `TEXT`, requiring casting.

**Bad Example:**
```sql
-- ai_conversations uses TEXT
CREATE TABLE ai_conversations (
  user_id TEXT  -- ❌ Inconsistent type
);

CREATE POLICY "select_own_ai_conversations" ON ai_conversations
  FOR SELECT USING (user_id = auth.uid()::text);  -- ❌ Requires casting
```

**Good Example:**
```sql
-- ✅ Always use UUID for user_id
CREATE TABLE ai_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id)
);

CREATE POLICY "select_own_ai_conversations" ON ai_conversations
  FOR SELECT USING (user_id = auth.uid());  -- ✅ No casting needed
```

**Fix:** Standardize on `UUID` for all `user_id` columns.

---

### Pitfall 4: Missing WITH CHECK Clauses

**Problem:** Users might update records to values that violate the policy.

**Bad Example:**
```sql
-- ❌ Missing WITH CHECK
CREATE POLICY "update_own_profiles" ON user_profiles
  FOR UPDATE USING (auth.uid() = user_id);
-- Vulnerability: User could UPDATE user_id to another user's ID
```

**Good Example:**
```sql
-- ✅ Both USING and WITH CHECK
CREATE POLICY "update_own_profiles" ON user_profiles
  FOR UPDATE
  USING (auth.uid() = user_id)  -- Can update if they own it
  WITH CHECK (auth.uid() = user_id);  -- Result must still be owned by them
```

**Fix:** Always include **both USING and WITH CHECK** for UPDATE/INSERT policies.

---

### Pitfall 5: Overly Broad Public Policies

**Problem:** Public policies without conditions expose all data.

**Bad Example:**
```sql
-- ❌ Exposes ALL job_skills (including deleted, draft, future-dated)
CREATE POLICY "public_read_job_skills" ON job_skills
  FOR SELECT USING (true);
```

**Good Example:**
```sql
-- ✅ Only show active, published skills
CREATE POLICY "public_read_job_skills" ON job_skills
  FOR SELECT USING (
    is_active = true
    AND status = 'published'
    AND published_at <= NOW()
  );
```

**Fix:** Add status checks, timestamp filters, soft-delete exclusions.

---

### Pitfall 6: Forgotten Service Role Bypass

**Problem:** Backend services can't perform operations because no service role policy exists.

**Symptoms:**
- Trigger functions fail with "permission denied"
- Backend services get empty result sets
- Migration scripts can't insert data

**Bad Example:**
```sql
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "select_own_notifications" ON notifications
  FOR SELECT USING (user_id = auth.uid());
-- ❌ No service role policy - backend can't send notifications
```

**Good Example:**
```sql
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "select_own_notifications" ON notifications
  FOR SELECT TO authenticated USING (user_id = auth.uid());

-- ✅ Service role can insert notifications for any user
CREATE POLICY "service_role_notifications" ON notifications
  FOR ALL TO service_role USING (true);

GRANT SELECT ON notifications TO authenticated;
GRANT ALL ON notifications TO service_role;
```

**Fix:** **Always** add service role bypass policy to every RLS-enabled table.

---

## Migration Examples

### Example 1: New Table with RLS from Day One

```sql
-- Migration: 20260110_create_user_achievements.sql
-- Issue: #123

-- Create table
CREATE TABLE user_achievements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  achievement_type TEXT NOT NULL,
  earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_earned_at ON user_achievements(earned_at DESC);

-- ✅ Enable RLS immediately (same migration)
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;

-- ✅ Apply policies (same migration)
CREATE POLICY "select_own_user_achievements"
  ON user_achievements
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "insert_own_user_achievements"
  ON user_achievements
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- No UPDATE/DELETE policies (achievements are immutable)

CREATE POLICY "service_role_user_achievements"
  ON user_achievements
  FOR ALL
  TO service_role
  USING (true);

-- Grant permissions
GRANT SELECT, INSERT ON user_achievements TO authenticated;
GRANT ALL ON user_achievements TO service_role;

-- Add comments
COMMENT ON TABLE user_achievements IS 'User achievements and milestones (recovery journey, job search progress)';
COMMENT ON COLUMN user_achievements.metadata IS 'Achievement-specific data (job_id, days_sober, etc.)';
```

---

### Example 2: Adding RLS to Existing Table

```sql
-- Migration: 20260110_add_rls_to_companies.sql
-- Issue: #124
-- Fixes security vulnerability: companies table lacks RLS

BEGIN;

-- Enable RLS
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- Public read (companies are discoverable for job searches)
CREATE POLICY "public_read_companies"
  ON companies
  FOR SELECT
  USING (
    status = 'active'
    AND is_approved = true
  );

-- Employers can manage their company profiles
CREATE POLICY "employer_manage_companies"
  ON companies
  FOR ALL
  TO authenticated
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- Service role bypass
CREATE POLICY "service_role_companies"
  ON companies
  FOR ALL
  TO service_role
  USING (true);

-- Grant permissions
GRANT SELECT ON companies TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON companies TO authenticated;
GRANT ALL ON companies TO service_role;

COMMIT;
```

---

### Example 3: Fixing Recursive Policy Issue

```sql
-- Migration: 20260110_fix_employer_profiles_rls.sql
-- Issue: #125
-- Fixes: "infinite recursion detected" when anonymous users view jobs

-- Problem: jobs table joins employer_profiles, but employer_profiles
-- has no policy allowing anonymous SELECT

BEGIN;

-- Add public read policy to employer_profiles
CREATE POLICY "public_read_employer_profiles"
  ON employer_profiles
  FOR SELECT
  USING (true);  -- All employer profiles are public (needed for job listings)

-- Existing owner policy remains unchanged
-- CREATE POLICY "owner_manage_employer_profiles" ON employer_profiles
--   FOR ALL TO authenticated USING (user_id = auth.uid());

COMMIT;
```

---

## Testing Requirements

### Automated RLS Test Suite

**All Tier 0 services** (HIPAA-compliant) **MUST** have automated RLS tests.

See [testing-rls-policies.md](testing-rls-policies.md) for comprehensive testing guide.

### Required Test Scenarios

1. **User Isolation Test**
   - User A cannot access User B's data
   - User A can access their own data

2. **Service Role Bypass Test**
   - Service role can access all data
   - Service role bypasses user-level restrictions

3. **Admin Role Test**
   - Admin can access admin-only tables
   - Non-admin cannot access admin-only tables

4. **Public Policy Test**
   - Anonymous users can view published content
   - Anonymous users cannot view draft/deleted content

5. **Child Resource Test**
   - Users can access child records via parent ownership
   - Users cannot access other users' child records

### Example Test (pytest + Supabase)

```python
# tests/security/test_rls_policies.py
import pytest
from supabase import create_client, Client

@pytest.fixture
def user_a_client() -> Client:
    """Supabase client authenticated as User A"""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.sign_in_with_password({"email": "user_a@test.com", "password": "test123"})
    return client

@pytest.fixture
def user_b_client() -> Client:
    """Supabase client authenticated as User B"""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.sign_in_with_password({"email": "user_b@test.com", "password": "test123"})
    return client

@pytest.fixture
def service_client() -> Client:
    """Supabase client with service role (bypasses RLS)"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_user_cannot_access_other_user_profiles(user_a_client, user_b_client, service_client):
    """User A cannot read User B's profile"""
    # Setup: Create User B's profile using service role
    user_b_profile = service_client.table("user_profiles").insert({
        "user_id": USER_B_ID,
        "bio": "User B's secret bio"
    }).execute().data[0]

    # Test: User A tries to read User B's profile
    result = user_a_client.table("user_profiles").select("*").eq("id", user_b_profile["id"]).execute()

    # Assert: User A gets empty result (RLS blocked access)
    assert len(result.data) == 0, "User A should not see User B's profile"

def test_service_role_bypasses_rls(service_client):
    """Service role can access all data regardless of ownership"""
    # Service role should see all profiles
    result = service_client.table("user_profiles").select("*").execute()
    assert len(result.data) > 0, "Service role should see all profiles"
```

### CI/CD Integration

```yaml
# .github/workflows/test-rls-policies.yml
name: RLS Policy Tests

on: [push, pull_request]

jobs:
  test-rls:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest supabase

      - name: Run RLS tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_TEST_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_TEST_ANON_KEY }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_TEST_SERVICE_KEY }}
        run: pytest tests/security/test_rls_policies.py -v
```

---

## Related Standards

- **[db-isolation-migrations.md](db-isolation-migrations.md)** - Database per service pattern (RLS policies must be service-specific)
- **[testing-tdd.md](testing-tdd.md)** - Testing requirements (85% coverage, RLS tests mandatory for Tier 0)
- **[testing-rls-policies.md](testing-rls-policies.md)** - Comprehensive RLS testing guide
- **[service-spec-template.md](service-spec-template.md)** - Service specification template (includes RLS checklist)
- **[security/api-gateway-networking.md](security/api-gateway-networking.md)** - API-level security (RLS complements API auth)
- **[language-tone.md](language-tone.md)** - Error messages (RLS denials should be supportive, not punitive)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-09 | Claude + Team | Initial standard based on analysis of 28 SQL files across Employa codebase |

---

## Approval

This standard was created based on comprehensive analysis of existing Employa RLS patterns and is ready for team review.

**Next Steps:**
1. Team review and feedback (3-5 business days)
2. Pilot implementation (verify Dave schema compliance)
3. Rollout to all services (update existing tables during next schema migration cycle)
