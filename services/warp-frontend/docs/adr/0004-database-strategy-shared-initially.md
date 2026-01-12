# ADR-0004: Database Strategy - Shared Warp DB Initially

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#344](https://github.com/employa-work/employa-web/issues/344)
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Context

Warp-frontend needs database access for:
- User profiles (job seekers, employers)
- Job postings
- Saved jobs, applications
- Recovery milestones (for job seekers in recovery)

Two options:
1. **Shared Database:** Use existing Warp Supabase project (`flisguvsodactmddejqz`)
2. **Dedicated Database:** Create new `warp-frontend-db` Supabase project

ProjectPhoenix standards recommend **per-service databases** for isolation, but this adds migration complexity for MVP.

---

## Decision

**We will start with the shared Warp database (`flisguvsodactmddejqz`), with planned migration to dedicated database when multi-tenancy requires it.**

### Database Details

- **Supabase Project:** `flisguvsodactmddejqz` (Warp DB)
- **Used By:** Warp (Next.js), CareerIntelligence, UserOnboarding, Outreach, CareerTools
- **Migration Timeline:** Phase 3+ (when employer multi-tenancy launches)

---

## Rationale

### Why Shared DB (For Now)

**1. Faster MVP Delivery**
- ✅ Database already exists (tables, RLS policies, seed data)
- ✅ No migration work needed (users, jobs, applications already there)
- ✅ Can start building features immediately

**2. Simpler Development**
- ✅ Single database to manage (for now)
- ✅ Existing RLS policies work (no need to recreate)
- ✅ Dev team already familiar with schema

**3. Cost Savings (MVP Stage)**
- ✅ One Supabase project ($0/month on free tier)
- ✅ Defer dedicated DB costs until needed

**4. Migration Path Exists**
- ✅ When multi-tenancy requires isolation, we can migrate
- ✅ ProjectPhoenix has migration scripts (Dave already migrated to dedicated DB)
- ✅ Data is in Supabase (easy to export/import)

### When to Migrate (Planned)

**Triggers for migration:**
1. **Multi-tenancy:** When employers need data isolation (e.g., employer A can't see employer B's job postings)
2. **RLS complexity:** When shared RLS policies become unmanageable
3. **Scale:** When database size impacts performance
4. **Compliance:** When HIPAA requires dedicated database per service

**Expected Timeline:** Phase 3+ (Q2 2026 or later)

---

## Alternatives Considered

### Option 1: Shared Warp DB ✅ **CHOSEN**

**Pros:**
- ✅ Zero migration work (start building today)
- ✅ Existing schema, RLS policies, seed data
- ✅ Cost savings ($0/month on free tier)
- ✅ Simpler for MVP

**Cons:**
- ⚠️ Eventual migration needed (tech debt)
- ⚠️ Shared RLS policies (less isolation)
- ⚠️ Multiple services share one database

**Verdict:** Best for MVP speed.

### Option 2: Dedicated DB Immediately ❌

**Pros:**
- ✅ Follows ProjectPhoenix standards
- ✅ Full isolation from day 1
- ✅ No migration later

**Cons:**
- ❌ Migration work before features (1-2 weeks delay)
- ❌ Recreate schema, RLS policies, seed data
- ❌ Additional Supabase project ($25/month when scaling)
- ❌ Slows MVP delivery

**Verdict:** Better for long-term, but delays MVP.

### Option 3: Hybrid (New Tables in Shared DB) ❌

**Pros:**
- ✅ Can add frontend-specific tables without migration

**Cons:**
- ❌ Still shared database (same RLS complexity)
- ❌ Still need migration later
- ❌ No real benefit over full shared approach

**Verdict:** No advantage over Option 1.

---

## Implementation

### Phase 1: Use Shared DB (Now)

1. **Configure Supabase client:**
   ```typescript
   // src/lib/supabase.ts
   import { createClient } from '@supabase/supabase-js';

   const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
   const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

   export const supabase = createClient(supabaseUrl, supabaseKey);
   ```

2. **Environment variables:**
   ```bash
   # .env.local (loaded from .env.workspace)
   NEXT_PUBLIC_SUPABASE_URL=https://flisguvsodactmddejqz.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<from-workspace-env>
   ```

3. **Use existing schema:**
   - Tables: `users`, `jobs`, `applications`, `saved_jobs`, `recovery_milestones`
   - RLS policies: Already configured (user-level isolation)

### Phase 2: Add Frontend-Specific Tables (If Needed)

If warp-frontend needs new tables:
```sql
-- Example: User preferences table
CREATE TABLE user_preferences (
  user_id UUID REFERENCES users(id) PRIMARY KEY,
  theme TEXT DEFAULT 'light',
  notifications_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS policy
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own preferences"
  ON user_preferences FOR SELECT
  USING (auth.uid() = user_id);
```

### Phase 3: Migrate to Dedicated DB (Future)

**When:** Multi-tenancy launch (Phase 3+)

**Process:**
1. Create new Supabase project: `warp-frontend-db`
2. Export schema from `flisguvsodactmddejqz`
3. Migrate data (users, jobs, applications)
4. Update RLS policies for multi-tenancy
5. Update env vars in warp-frontend
6. Deploy and test
7. Monitor for 1 week
8. Decommission old tables in shared DB

**Estimated Effort:** 1-2 weeks (based on Dave migration)

---

## Consequences

### Positive

1. **Immediate Start:** No migration delays, build features today
2. **Cost Savings:** $0/month until we need dedicated DB
3. **Simpler Setup:** One database, one set of credentials
4. **Proven Schema:** Existing schema works, no need to recreate

### Negative

1. **Tech Debt:** Will need migration in Phase 3+
2. **Shared RLS:** Less isolation than dedicated DB
3. **Multi-Service Risk:** If one service breaks DB, all affected (low risk in practice)

### Neutral

1. **Migration Path:** Clear path to dedicated DB when needed
2. **ProjectPhoenix Standards:** Temporary deviation (acceptable for MVP)

---

## Migration Criteria

**Migrate to dedicated DB when ANY of these occur:**

1. **Multi-tenancy required:** Employers need strict data isolation
2. **RLS complexity:** Shared RLS policies become unmanageable (>50 policies)
3. **Performance issues:** Database size impacts query performance (>100GB)
4. **Compliance audit:** HIPAA requires dedicated database per service
5. **Team request:** Engineering team requests dedicated DB

**Expected Trigger:** Multi-tenancy (employer features launch)

---

## Success Metrics

- **Development Velocity:** Features shipped without database delays
- **RLS Policy Count:** Stay under 50 policies (manageable complexity)
- **Query Performance:** p95 latency < 100ms for common queries
- **Cost:** $0/month on Supabase free tier (up to 500MB database)

---

## References

- **Warp Supabase Project:** https://flisguvsodactmddejqz.supabase.co
- **Dave Migration:** `Dave/DATABASE-MIGRATION-COMPLETE.md` (example of dedicated DB migration)
- **ProjectPhoenix Standards:** Recommend per-service databases (we defer to Phase 3+)

---

## Notes

- **This is a pragmatic decision:** Speed to MVP > architectural purity
- **Migration is planned, not forgotten:** Phase 3+ timeline documented
- **Dave already uses dedicated DB:** We have migration experience
- **Supabase export/import is simple:** Migration is low-risk
- **Free tier limits:** 500MB database, 2GB bandwidth/month (sufficient for MVP)
