# ADR-0003: State Management - Zustand + TanStack Query

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#344](https://github.com/employa-work/employa-web/issues/344)
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Context

Warp-frontend needs client-side state management for:
- **Client State:** UI preferences, form state, auth tokens (browser-only data)
- **Server State:** API responses, cached data, optimistic updates (data from backend)

Requirements:
- Minimal boilerplate (no Redux ceremony)
- TypeScript-first (type safety without manual typing)
- Works with Next.js App Router (Server Components + Client Components)
- Handles API caching, refetching, optimistic updates
- Small bundle size (performance for job seekers on slow connections)

---

## Decision

**We will use:**
1. **Zustand** for client state (UI, preferences, auth)
2. **TanStack Query** (formerly React Query) for server state (API data, caching)

### Separation of Concerns

| State Type | Tool | Examples |
|------------|------|----------|
| **Client State** | Zustand | UI sidebar open/closed, theme preference, form draft state, auth token |
| **Server State** | TanStack Query | Job listings, user profile, saved jobs, application status |

---

## Rationale

### Zustand for Client State

**Why Zustand:**
- ✅ **Minimal API:** 1-2 lines to create a store (vs 20+ for Redux)
- ✅ **No Context Providers:** Direct import and use (no `<Provider>` wrapper)
- ✅ **TypeScript-first:** Automatic type inference
- ✅ **Tiny bundle:** 1.2kb gzipped (vs 43kb for Redux + RTK)
- ✅ **Works with RSC:** Server Components can read initial state, Client Components mutate

**Example:**
```typescript
// src/stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));

// Usage in any component
import { useUIStore } from '@/stores/uiStore';

function Sidebar() {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  // ...
}
```

### TanStack Query for Server State

**Why TanStack Query:**
- ✅ **Purpose-built for server state:** Caching, refetching, stale-while-revalidate
- ✅ **Optimistic updates:** Update UI before API responds (feels instant)
- ✅ **Automatic refetching:** Re-fetch on window focus, network reconnect
- ✅ **TypeScript-first:** Full type safety for API responses
- ✅ **DevTools:** Inspect cache, queries, mutations in browser
- ✅ **Small bundle:** 12kb gzipped (vs 43kb for Redux + RTK Query)

**Example:**
```typescript
// src/hooks/useJobs.ts
import { useQuery } from '@tanstack/react-query';

interface Job {
  id: string;
  title: string;
  company: string;
}

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: async (): Promise<Job[]> => {
      const res = await fetch('/api/jobs');
      return res.json();
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Usage
function JobList() {
  const { data: jobs, isLoading, error } = useJobs();
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{jobs.map(job => <JobCard key={job.id} job={job} />)}</div>;
}
```

### Why Not Redux?

**Redux Toolkit Query (RTK Query) could handle both, but:**
- ❌ **Heavy boilerplate:** Slices, reducers, actions, thunks
- ❌ **Large bundle:** 43kb gzipped (vs 1.2kb Zustand + 12kb TanStack Query = 13.2kb)
- ❌ **Context Provider required:** Wraps entire app
- ❌ **Overkill:** Designed for complex enterprise apps (Employa is MVP-stage)

**Redux is great for:**
- Large teams (100+ developers)
- Complex state machines
- Time-travel debugging requirements

**Employa doesn't need:**
- Redux DevTools time-travel (TanStack Query DevTools sufficient)
- Middleware ecosystem (we use simple async/await)
- Centralized store architecture (Zustand's granular stores are cleaner)

---

## Alternatives Considered

### Option 1: Context API ❌

**Pros:**
- Built into React (no dependencies)

**Cons:**
- ❌ Re-renders entire tree on state change (performance issue)
- ❌ Boilerplate (`createContext`, `useContext`, providers)
- ❌ No caching, refetching, or optimistic updates (need manual implementation)
- ❌ Not designed for server state (API data)

**Verdict:** Good for simple theme/auth context, not for app-wide state.

### Option 2: Redux Toolkit + RTK Query ❌

**Pros:**
- ✅ Industry standard (large ecosystem)
- ✅ Powerful DevTools

**Cons:**
- ❌ 43kb bundle size (3x larger than Zustand + TanStack Query)
- ❌ High boilerplate (slices, reducers, configureStore)
- ❌ Overkill for MVP-stage app

**Verdict:** Too heavy for Employa's needs.

### Option 3: Zustand + TanStack Query ✅ **CHOSEN**

(See Decision section above)

**Pros:**
- ✅ Minimal boilerplate (Zustand: 1-2 lines per store)
- ✅ Small bundle (13.2kb total)
- ✅ Purpose-built tools (client state + server state)
- ✅ TypeScript-first
- ✅ Works perfectly with Next.js App Router

### Option 4: Jotai + TanStack Query ❌

**Jotai:** Atomic state management (similar to Recoil)

**Pros:**
- ✅ Tiny bundle (3kb)
- ✅ Fine-grained reactivity (atoms)

**Cons:**
- ⚠️ Less mature than Zustand (newer library)
- ⚠️ Atomic model adds complexity (overkill for Employa)
- ⚠️ Team unfamiliarity (Zustand is more widely known)

**Verdict:** Great library, but Zustand is simpler and more established.

---

## Implementation Plan

### Phase 1: Setup TanStack Query

1. **Install dependencies:**
   ```bash
   npm install @tanstack/react-query @tanstack/react-query-devtools
   ```

2. **Create QueryClient provider:**
   ```typescript
   // src/lib/queryClient.ts
   import { QueryClient } from '@tanstack/react-query';

   export const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 1000 * 60 * 5, // 5 minutes
         retry: 1,
       },
     },
   });
   ```

3. **Wrap app in provider:**
   ```typescript
   // app/layout.tsx
   'use client';
   import { QueryClientProvider } from '@tanstack/react-query';
   import { queryClient } from '@/lib/queryClient';

   export default function RootLayout({ children }) {
     return (
       <QueryClientProvider client={queryClient}>
         {children}
       </QueryClientProvider>
     );
   }
   ```

### Phase 2: Setup Zustand

1. **Install dependencies:**
   ```bash
   npm install zustand
   ```

2. **Create first store (auth):**
   ```typescript
   // src/stores/authStore.ts
   import { create } from 'zustand';
   import { persist } from 'zustand/middleware';

   interface AuthState {
     user: User | null;
     setUser: (user: User | null) => void;
     logout: () => void;
   }

   export const useAuthStore = create<AuthState>()(
     persist(
       (set) => ({
         user: null,
         setUser: (user) => set({ user }),
         logout: () => set({ user: null }),
       }),
       { name: 'auth-storage' } // Persist to localStorage
     )
   );
   ```

### Phase 3: Create API Hooks (TanStack Query)

```typescript
// src/hooks/api/useJobs.ts
export function useJobs() { /* ... */ }
export function useSaveJob() { /* ... */ }

// src/hooks/api/useProfile.ts
export function useProfile() { /* ... */ }
export function useUpdateProfile() { /* ... */ }
```

### Phase 4: Create Client State Stores (Zustand)

```typescript
// src/stores/uiStore.ts - UI preferences
// src/stores/authStore.ts - Auth state (already created)
// src/stores/formStore.ts - Form draft state (if needed)
```

---

## Consequences

### Positive

1. **Minimal Boilerplate:** Zustand stores are 5-10 lines (vs 50+ for Redux)
2. **Small Bundle:** 13.2kb total (vs 43kb for Redux)
3. **TypeScript-First:** Automatic type inference, no manual typing
4. **Developer Experience:** Simple APIs, excellent DevTools
5. **Performance:** Fine-grained reactivity (only re-render what changed)
6. **Server State Management:** TanStack Query handles caching, refetching automatically

### Negative

1. **Two Libraries:** Team must learn both Zustand and TanStack Query
   - **Mitigation:** Both have minimal APIs (1-2 hours to learn each)
2. **Less Ecosystem:** Smaller than Redux (fewer middleware, plugins)
   - **Mitigation:** We don't need Redux's ecosystem (simple app)

### Neutral

1. **DevTools:** TanStack Query DevTools excellent, Zustand has basic DevTools
2. **Persistence:** Zustand `persist` middleware for localStorage (simple to use)

---

## Success Metrics

- **Bundle Size:** Client state + server state libraries < 15kb gzipped
- **Developer Velocity:** New API hook created in <10 minutes
- **Type Safety:** 100% of state interactions are type-safe (no `any`)
- **Cache Hit Rate:** >70% of API requests served from TanStack Query cache

---

## References

- **Zustand:** https://github.com/pmndrs/zustand
- **TanStack Query:** https://tanstack.com/query/latest
- **Comparison:** https://tanstack.com/query/latest/docs/react/comparison
- **Next.js + TanStack Query:** https://tanstack.com/query/latest/docs/react/guides/ssr

---

## Notes

- **Server Components:** Can't use hooks. Pass fetched data as props to Client Components.
- **Prefetching:** Use TanStack Query's `prefetchQuery` in Server Components for instant page loads.
- **Optimistic Updates:** Use `useMutation` with `onMutate` for instant UI feedback.
- **Persistence:** Use Zustand's `persist` middleware for client state (theme, auth tokens).
