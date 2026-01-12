# ADR-0002: App Router Directory Structure

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#344](https://github.com/employa-work/employa-web/issues/344)
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Context

Next.js 15 App Router provides flexible directory structure conventions. We need to establish a standard structure that:
- Scales as the application grows (MVP → multi-user-type platform)
- Makes feature ownership clear
- Supports multiple user types (job seekers, employers, admins)
- Keeps shared code organized and discoverable

---

## Decision

**We will use feature-based route grouping with a separate `src/` directory for shared code.**

### Directory Structure

```
warp-frontend/
├── src/
│   ├── components/          # Shared UI components
│   │   ├── ui/              # Base components (Button, Input, Card)
│   │   ├── forms/           # Form components (FormField, ValidationMessage)
│   │   └── layout/          # Layout components (Header, Footer, Nav)
│   ├── lib/                 # Utilities and helpers
│   │   ├── logger.ts        # Custom logger with PHI redaction
│   │   ├── supabase.ts      # Supabase client
│   │   └── utils.ts         # Common utilities
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts       # Authentication hook
│   │   └── useFormState.ts  # Form state management
│   ├── stores/              # Zustand stores (client state)
│   │   ├── authStore.ts     # Auth state
│   │   └── uiStore.ts       # UI preferences
│   └── types/               # Shared TypeScript types
│       ├── api.ts           # API response types
│       └── models.ts        # Domain models
│
├── app/
│   ├── (auth)/              # Authentication routes (grouped)
│   │   ├── login/           # /login
│   │   ├── register/        # /register
│   │   └── forgot-password/ # /forgot-password
│   ├── (jobs)/              # Job search routes (grouped)
│   │   ├── search/          # /search
│   │   ├── [jobId]/         # /[jobId] (dynamic job detail)
│   │   └── saved/           # /saved
│   ├── (profile)/           # User profile routes (grouped)
│   │   ├── settings/        # /settings
│   │   ├── recovery/        # /recovery (recovery milestones)
│   │   └── applications/    # /applications
│   ├── (employer)/          # Employer routes (grouped, future)
│   │   ├── dashboard/       # /dashboard
│   │   └── post-job/        # /post-job
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Homepage (/)
│   └── globals.css          # Global styles
```

### Route Grouping Convention

- **Grouped routes:** `(groupName)/` - Parentheses prevent group name from appearing in URL
- **Example:** `app/(auth)/login/page.tsx` → URL: `/login` (not `/auth/login`)
- **Purpose:** Logical grouping without affecting URL structure

---

## Rationale

### Feature-Based Grouping

**Why:**
- ✅ **Scalability:** Easy to add new features without restructuring
- ✅ **Ownership:** Clear boundaries for feature teams
- ✅ **Discoverability:** Related routes grouped together
- ✅ **Flexibility:** Routes don't reflect folder structure (group names hidden)

**Example:**
```
app/(jobs)/search/page.tsx       → /search
app/(jobs)/[jobId]/page.tsx      → /[jobId]
app/(jobs)/saved/page.tsx        → /saved
```

All job-related routes grouped under `(jobs)` but URLs remain clean.

### Separate `src/` Directory

**Why:**
- ✅ **Clear separation:** `app/` = routes, `src/` = shared code
- ✅ **Import paths:** `@/components/Button` vs `../../components/Button`
- ✅ **Discoverability:** All shared code in one place
- ✅ **Convention:** Standard Next.js pattern (optional but recommended)

**Alternative (rejected):** `app/_components/`, `app/_lib/`, etc.
- ❌ Mixes routes and shared code in `app/` directory
- ❌ Less discoverable (underscore-prefixed directories harder to find)

### Multi-User-Type Support

**Current:** Job seekers only
**Future:** Employers, admins

**Strategy:**
- `(profile)/` - Job seeker routes
- `(employer)/` - Employer routes (future)
- `(admin)/` - Admin routes (future)

**Why not user-type-based top-level routing?**
- ❌ `app/(job-seeker)/`, `app/(employer)/` forces URLs like `/job-seeker/search`
- ✅ Feature grouping allows `/search` (job seeker) and `/employer/dashboard` (employer)

---

## Alternatives Considered

### Option 1: Flat Structure ❌

```
app/
├── login/
├── register/
├── search/
├── settings/
└── ...
```

**Pros:**
- Simple, minimal nesting

**Cons:**
- ❌ Doesn't scale (50+ routes become unmanageable)
- ❌ No logical grouping (auth, jobs, profile mixed together)
- ❌ Hard to assign ownership ("who owns login vs search?")

**Verdict:** Only viable for <10 routes.

### Option 2: User-Type-Based Grouping ❌

```
app/
├── (job-seeker)/
│   ├── search/
│   └── profile/
├── (employer)/
│   └── dashboard/
```

**Pros:**
- Clear user type separation

**Cons:**
- ❌ Forces URLs like `/job-seeker/search` (unless using rewrites)
- ❌ Shared routes unclear (homepage, about, pricing)
- ❌ Less flexible than feature grouping

**Verdict:** Better for multi-tenant SaaS with strict isolation.

### Option 3: Feature-Based (No `src/`) ❌

```
app/
├── (auth)/
├── (jobs)/
├── _components/    # Shared components
├── _lib/           # Shared utilities
└── _hooks/         # Shared hooks
```

**Pros:**
- All code in `app/` directory

**Cons:**
- ❌ Mixes routes and shared code
- ❌ Underscore-prefixed directories harder to discover
- ❌ Longer import paths from nested routes

**Verdict:** Acceptable but `src/` is cleaner.

### Option 4: Feature-Based + `src/` ✅ **CHOSEN**

(See Decision section above)

**Pros:**
- ✅ Scalable grouping
- ✅ Clean separation (routes vs shared code)
- ✅ Short import paths (`@/components/...`)
- ✅ Standard Next.js convention

---

## Implementation

### Step 1: Configure `tsconfig.json`

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/app/*": ["./app/*"]
    }
  }
}
```

**Enables:**
- `import { Button } from '@/components/ui/Button'`
- `import { logger } from '@/lib/logger'`

### Step 2: Create Directory Structure

```bash
mkdir -p src/{components/{ui,forms,layout},lib,hooks,stores,types}
mkdir -p app/{(auth),(jobs),(profile)}
```

### Step 3: Migrate Existing Code

Move spike code to new structure:
- `app/page.tsx` → Keep (homepage)
- `app/layout.tsx` → Keep (root layout)
- `app/globals.css` → Keep (global styles)

### Step 4: Add First Routes

Start with authentication:
```bash
mkdir -p app/(auth)/{login,register}
touch app/(auth)/login/page.tsx
touch app/(auth)/register/page.tsx
```

---

## Consequences

### Positive

1. **Scalable:** Can grow to 100+ routes without restructuring
2. **Clear Ownership:** Feature groups map to team responsibilities
3. **Clean URLs:** Route groups don't pollute URLs
4. **Discoverable:** Shared code in `src/`, routes in `app/`
5. **Standard:** Follows Next.js recommended patterns

### Negative

1. **Initial Complexity:** More directories upfront than flat structure
2. **Learning Curve:** Team needs to understand route grouping convention

### Neutral

1. **Group Naming:** Must decide on group names (`(auth)` vs `(authentication)`)
   - **Decision:** Use short names (`auth`, `jobs`, `profile`)

---

## Success Metrics

- **Developer Velocity:** New routes added in <5 minutes (using convention)
- **Discoverability:** Developers find shared components without asking (measure via onboarding feedback)
- **Import Path Length:** Average <3 segments (`@/components/ui/Button` vs `../../src/components/ui/Button`)

---

## References

- **Next.js App Router Docs:** https://nextjs.org/docs/app/building-your-application/routing
- **Route Groups:** https://nextjs.org/docs/app/building-your-application/routing/route-groups
- **Project Organization:** https://nextjs.org/docs/app/building-your-application/routing/colocation

---

## Notes

- Route groups `(name)` are optional but highly recommended for organization
- `src/` directory is optional in Next.js 15 but we choose to use it
- This structure can evolve (e.g., add `(employer)/` when employer features launch)
- Avoid over-nesting (max 3 levels: `app/(group)/[param]/page.tsx`)
