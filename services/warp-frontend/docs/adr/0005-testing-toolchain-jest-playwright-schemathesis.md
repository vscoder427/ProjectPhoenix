# ADR-0005: Testing Toolchain - Jest + Playwright + Schemathesis

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#344](https://github.com/employa-work/employa-web/issues/344)
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Context

Warp-frontend needs comprehensive testing coverage:
- **Unit/Component Tests:** React components, utilities, hooks
- **Integration Tests:** User flows, form submissions, navigation
- **E2E Tests:** Critical paths (login → search jobs → apply)
- **API Contract Tests:** Ensure backend APIs match frontend expectations

Requirements:
- **85% coverage minimum** (enforced in CI)
- **Fast feedback** (unit tests < 10s, E2E < 2 minutes)
- **TypeScript support** (type-safe tests)
- **Next.js 15 compatibility** (App Router, Server Components)
- **CI/CD integration** (GitHub Actions)

---

## Decision

**We will use:**
1. **Jest** for unit and component tests
2. **Playwright** for end-to-end (E2E) tests
3. **Schemathesis** for API contract tests (Phase 2+)

### Toolchain Breakdown

| Test Type | Tool | Scope | When to Run |
|-----------|------|-------|-------------|
| **Unit** | Jest | Functions, utilities | Every commit (pre-commit hook) |
| **Component** | Jest + React Testing Library | React components | Every commit |
| **Integration** | Playwright | User flows (multi-page) | Every PR |
| **E2E** | Playwright | Critical paths (login → apply) | Every PR, pre-deploy |
| **API Contract** | Schemathesis | API schema validation | Every PR (Phase 2+) |

---

## Rationale

### Jest for Unit/Component Tests

**Why Jest:**
- ✅ **Next.js Official Recommendation:** First-class Next.js support
- ✅ **Fast:** 100+ tests in <10 seconds
- ✅ **TypeScript Support:** Type-safe tests with `ts-jest`
- ✅ **Snapshot Testing:** Catch unintended UI changes
- ✅ **Coverage Built-In:** `--coverage` flag generates reports
- ✅ **Great DX:** Watch mode, parallel execution, clear error messages

**Example:**
```typescript
// src/components/ui/Button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    screen.getByText('Click me').click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
```

### Playwright for E2E Tests

**Why Playwright:**
- ✅ **Multi-Browser:** Chrome, Firefox, Safari, Edge
- ✅ **Fast Execution:** Parallelization, auto-waiting
- ✅ **TypeScript-First:** Native TypeScript support
- ✅ **Next.js Integration:** Can test production builds
- ✅ **Auto-Waiting:** No `sleep()` or manual waits needed
- ✅ **Trace Viewer:** Debug failed tests with video/screenshots

**Why Not Cypress:**
- ❌ Slower execution (no true parallelization)
- ❌ No multi-browser support on free tier
- ❌ Different API (team already knows Playwright from backend)

**Example:**
```typescript
// tests/e2e/job-search.spec.ts
import { test, expect } from '@playwright/test';

test('job seeker can search and apply', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  // Search jobs
  await page.goto('/search');
  await page.fill('[name="search"]', 'software engineer');
  await page.click('button:has-text("Search")');

  // Apply to first job
  await page.click('text="View Details"').first();
  await page.click('button:has-text("Apply")');

  // Verify success
  await expect(page.locator('text="Application submitted"')).toBeVisible();
});
```

### Schemathesis for API Contract Tests

**Why Schemathesis (Phase 2+):**
- ✅ **OpenAPI-Based:** Generates tests from API spec
- ✅ **Property-Based Testing:** Finds edge cases automatically
- ✅ **Fast Feedback:** Catches API breaking changes before deploy
- ✅ **Backend Consistency:** Employa backend services use Schemathesis

**When to Add:**
- Phase 2 (when warp-frontend calls backend APIs)
- After backend publishes OpenAPI specs

**Example:**
```python
# tests/api/test_jobs_api.py
import schemathesis

schema = schemathesis.from_uri("https://api.employa.work/openapi.json")

@schema.parametrize()
def test_jobs_api(case):
    case.call_and_validate()  # Auto-generates requests, validates responses
```

---

## Alternatives Considered

### Option 1: Vitest Instead of Jest ❌

**Vitest:** Modern Vite-native test runner

**Pros:**
- ✅ Faster than Jest (Vite's HMR)
- ✅ ESM-first (better module support)

**Cons:**
- ❌ Less mature than Jest (newer library)
- ❌ Smaller ecosystem (fewer plugins)
- ❌ Next.js official docs recommend Jest
- ❌ Team unfamiliarity (Jest is standard)

**Verdict:** Jest is safer choice for Next.js.

### Option 2: Cypress Instead of Playwright ❌

**Pros:**
- ✅ Great DX (interactive test runner)
- ✅ Time-travel debugging

**Cons:**
- ❌ Slower execution (no true parallelization)
- ❌ No Safari/Edge support on free tier
- ❌ Different syntax (team knows Playwright)
- ❌ Heavier setup (separate server process)

**Verdict:** Playwright is faster and more flexible.

### Option 3: Jest + Playwright + Schemathesis ✅ **CHOSEN**

(See Decision section above)

**Pros:**
- ✅ Jest for fast unit/component tests
- ✅ Playwright for robust E2E tests
- ✅ Schemathesis for API contract validation
- ✅ All tools work together in CI/CD

---

## Implementation Plan

### Phase 1: Jest Setup (Week 1)

1. **Install dependencies:**
   ```bash
   npm install --save-dev jest @testing-library/react @testing-library/jest-dom \
     @testing-library/user-event ts-jest @types/jest
   ```

2. **Configure Jest:**
   ```javascript
   // jest.config.js
   module.exports = {
     testEnvironment: 'jsdom',
     setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
     moduleNameMapper: {
       '^@/(.*)$': '<rootDir>/src/$1',
     },
     collectCoverageFrom: [
       'src/**/*.{ts,tsx}',
       '!src/**/*.d.ts',
       '!src/**/*.stories.tsx',
     ],
     coverageThreshold: {
       global: {
         branches: 85,
         functions: 85,
         lines: 85,
         statements: 85,
       },
     },
   };
   ```

3. **Add npm scripts:**
   ```json
   {
     "scripts": {
       "test": "jest",
       "test:watch": "jest --watch",
       "test:coverage": "jest --coverage"
     }
   }
   ```

4. **Write sample tests:** Start with `Button.test.tsx`, `utils.test.ts`

### Phase 2: Playwright Setup (Week 1)

1. **Install Playwright:**
   ```bash
   npm install --save-dev @playwright/test
   npx playwright install
   ```

2. **Configure Playwright:**
   ```typescript
   // playwright.config.ts
   import { defineConfig } from '@playwright/test';

   export default defineConfig({
     testDir: './tests/e2e',
     fullyParallel: true,
     retries: 2,
     use: {
       baseURL: 'http://localhost:3000',
       trace: 'on-first-retry',
     },
     projects: [
       { name: 'chromium', use: { browserName: 'chromium' } },
       { name: 'firefox', use: { browserName: 'firefox' } },
     ],
   });
   ```

3. **Add npm script:**
   ```json
   {
     "scripts": {
       "test:e2e": "playwright test"
     }
   }
   ```

4. **Write sample E2E test:** `tests/e2e/homepage.spec.ts`

### Phase 3: CI/CD Integration (Week 1-2)

**GitHub Actions workflow:**
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run test:coverage
      - run: npx codecov # Upload coverage to Codecov (optional)

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npm run test:e2e
```

### Phase 4: Schemathesis (Phase 2+)

**When backend APIs exist:**
```bash
pip install schemathesis
schemathesis run https://api.employa.work/openapi.json --checks all
```

---

## Consequences

### Positive

1. **High Coverage:** 85% minimum enforced in CI (prevents regressions)
2. **Fast Feedback:** Unit tests < 10s, E2E < 2 minutes
3. **Multi-Browser:** Playwright tests Chrome, Firefox, Safari
4. **Type Safety:** All tests are TypeScript (catch errors at compile-time)
5. **Standard Tools:** Jest and Playwright are industry standard
6. **API Contracts:** Schemathesis ensures frontend/backend alignment

### Negative

1. **Initial Setup:** ~1-2 weeks to configure all tools
2. **Learning Curve:** Team must learn 3 tools (Jest, Playwright, Schemathesis)
   - **Mitigation:** Documentation + pair programming
3. **CI Time:** Full test suite may take 5-10 minutes
   - **Mitigation:** Run unit tests on every commit, E2E on PR only

### Neutral

1. **Coverage Threshold:** 85% is aggressive but achievable
2. **Test Maintenance:** Tests need updates when features change (expected)

---

## Testing Strategy

### What to Test

**Unit Tests (Jest):**
- ✅ Utility functions (`formatDate`, `validateEmail`)
- ✅ React hooks (`useAuth`, `useFormState`)
- ✅ Components (`Button`, `Input`, `Card`)
- ❌ API calls (mock with `jest.mock()`)

**Component Tests (Jest + React Testing Library):**
- ✅ User interactions (click, type, submit)
- ✅ Conditional rendering (loading states, error states)
- ✅ Props validation
- ❌ E2E flows (use Playwright)

**E2E Tests (Playwright):**
- ✅ Critical paths (login → search → apply)
- ✅ Multi-page flows
- ✅ Authentication flows
- ❌ Every possible edge case (too slow)

**API Contract Tests (Schemathesis):**
- ✅ API response schema validation
- ✅ Error handling (4xx, 5xx responses)
- ✅ Edge cases (empty arrays, null values)

### What NOT to Test

- ❌ Third-party libraries (trust Supabase, Zustand, TanStack Query)
- ❌ Next.js internals (trust Next.js)
- ❌ Trivial code (one-liners, getters/setters)

---

## Success Metrics

- **Coverage:** 85% minimum (enforced in CI)
- **Test Count:** 200+ tests by end of Phase 2
- **CI Pass Rate:** >95% (tests are reliable, not flaky)
- **Test Execution Time:** Unit tests < 10s, E2E < 2 minutes
- **Regression Rate:** <5% (caught by tests before deploy)

---

## References

- **Jest + Next.js:** https://nextjs.org/docs/app/building-your-application/testing/jest
- **Playwright:** https://playwright.dev/
- **React Testing Library:** https://testing-library.com/react
- **Schemathesis:** https://schemathesis.readthedocs.io/

---

## Notes

- **Pre-commit hook:** Run `npm test` before every commit (fast feedback)
- **Visual regression testing:** Defer to Phase 3+ (e.g., Chromatic, Percy)
- **Accessibility testing:** Use `jest-axe` for a11y checks in component tests
- **Mocking:** Use `msw` (Mock Service Worker) for API mocking in tests
