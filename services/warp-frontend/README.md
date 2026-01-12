# Warp Frontend

**Recovery-focused job search platform built with Next.js 15 and shadcn/ui**

**Status:** Phase 1 Pre-Development Complete ✅
**Epic:** [#327](https://github.com/employa-work/employa-web/issues/327)

---

## Overview

Warp is Employa's flagship web application connecting job seekers in recovery with recovery-friendly employers. Built with elderly-friendly design principles, WCAG AAA accessibility, and HIPAA-compliant observability.

### Key Features (Phase 1)

- ✅ **Next.js 15 App Router** with Server Components and SSR
- ✅ **shadcn/ui Component Library** (23+ accessible components)
- ✅ **Elderly-Friendly Design** (18px base font, 48px touch targets, WCAG AAA)
- ✅ **Recovery-Focused UX** (calming language, supportive error messages)
- ✅ **HIPAA-Compliant Observability** (Sentry + custom logger with PHI redaction)
- ✅ **85% Test Coverage** (Jest + Playwright, enforced in CI)
- ✅ **Production-Ready Architecture** (5 ADRs documenting all major decisions)

---

## Quick Start

### Prerequisites

- Node.js 22+
- npm 10+

### Development Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

### Environment Variables

Create `.env.local` with:

```bash
# Supabase (shared Warp DB)
NEXT_PUBLIC_SUPABASE_URL=https://flisguvsodactmddejqz.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Sentry (observability)
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
SENTRY_ORG=your-org
SENTRY_PROJECT=warp-frontend
SENTRY_AUTH_TOKEN=your-auth-token
```

See [`.env.workspace`](../../.env.workspace) in workspace root for all credentials.

---

## Project Structure

```
warp-frontend/
├── app/                          # Next.js 15 App Router
│   ├── layout.tsx                # Root layout with Web Vitals
│   └── page.tsx                  # Homepage
├── src/
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components (23+)
│   │   ├── forms/                # Custom form helpers
│   │   └── web-vitals.tsx        # Performance monitoring
│   └── lib/
│       ├── utils.ts              # Utility functions
│       ├── logger.ts             # HIPAA-compliant logger
│       └── logger.test.ts        # PHI redaction tests
├── docs/
│   ├── adr/                      # Architecture Decision Records
│   │   ├── 0001-hosting-platform-cloud-run-cdn.md
│   │   ├── 0002-app-router-directory-structure.md
│   │   ├── 0003-state-management-zustand-tanstack-query.md
│   │   ├── 0004-database-strategy-shared-initially.md
│   │   └── 0005-testing-toolchain-jest-playwright-schemathesis.md
│   ├── component-library.md      # Component usage guide
│   ├── design-philosophy.md      # Recovery-focused UX principles
│   ├── observability.md          # Sentry + logger guide
│   └── testing-guide.md          # Testing patterns and examples
├── tests/
│   └── e2e/                      # Playwright E2E tests
├── sentry.{client,server,edge}.config.ts  # Sentry with PHI redaction
├── instrumentation.ts            # Next.js 15 instrumentation
├── jest.config.js                # Jest configuration (85% coverage)
├── playwright.config.ts          # Playwright configuration
└── tailwind.config.ts            # Tailwind with design tokens
```

---

## Tech Stack

### Core

- **Framework:** Next.js 15 (App Router, Server Components, SSR)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 3
- **Components:** shadcn/ui (Radix UI primitives)

### State Management (ADR-0003)

- **Client State:** Zustand (global UI state)
- **Server State:** TanStack Query (API caching, optimistic updates)

### Database (ADR-0004)

- **Provider:** Supabase (PostgreSQL)
- **Strategy:** Shared Warp DB initially (`flisguvsodactmddejqz`)
- **Future:** Dedicated DB when multi-tenancy required (Phase 3+)

### Observability (ADR-0005)

- **Error Tracking:** Sentry (client + server + edge)
- **Performance:** Sentry + Web Vitals (LCP, FID, CLS, TTFB, FCP, INP)
- **Logging:** Custom logger with allowlist-based PHI redaction

### Testing

- **Unit/Component:** Jest + React Testing Library
- **E2E:** Playwright (Chrome, Firefox, Safari)
- **Coverage:** 85% minimum (enforced in CI)
- **API Contracts:** Schemathesis (Phase 2+)

### Deployment (ADR-0001)

- **Platform:** Cloud Run + CDN (planned)
- **CI/CD:** GitHub Actions
- **IaC:** Terraform (planned)

---

## Scripts

### Development

```bash
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server
npm run lint             # Run ESLint
```

### Testing

```bash
npm test                 # Run Jest tests
npm run test:watch       # Run Jest in watch mode
npm run test:coverage    # Run Jest with coverage report
npm run test:e2e         # Run Playwright E2E tests
npm run test:e2e:ui      # Run Playwright with UI
```

### Code Quality

```bash
npm run lint             # ESLint check
npm run lint:fix         # ESLint auto-fix
npm run type-check       # TypeScript type check
```

---

## Documentation

### Architecture Decision Records (ADRs)

1. **[ADR-0001: Cloud Run + CDN](docs/adr/0001-hosting-platform-cloud-run-cdn.md)**
   Why Cloud Run + CDN over Firebase Hosting

2. **[ADR-0002: App Router Directory Structure](docs/adr/0002-app-router-directory-structure.md)**
   Feature-based structure with `src/` directory

3. **[ADR-0003: State Management](docs/adr/0003-state-management-zustand-tanstack-query.md)**
   Zustand (client) + TanStack Query (server)

4. **[ADR-0004: Database Strategy](docs/adr/0004-database-strategy-shared-initially.md)**
   Shared Warp DB initially, migrate to dedicated DB later

5. **[ADR-0005: Testing Toolchain](docs/adr/0005-testing-toolchain-jest-playwright-schemathesis.md)**
   Jest + Playwright + Schemathesis

### Guides

- **[Component Library Guide](docs/component-library.md)** - shadcn/ui components, design tokens, usage patterns
- **[Design Philosophy](docs/design-philosophy.md)** - Recovery-focused UX principles
- **[Testing Guide](docs/testing-guide.md)** - Unit, component, E2E testing patterns
- **[Observability Guide](docs/observability.md)** - Sentry, logger, Web Vitals, HIPAA compliance

---

## Design System

### Design Tokens

**Typography:**
```css
--font-base: 18px (line-height: 1.6)  /* Elderly-friendly */
--font-heading-1: 2.5rem
--font-heading-2: 2rem
--font-heading-3: 1.75rem
```

**Touch Targets:**
```css
--spacing-touch: 48px  /* Minimum touch target size */
```

**Colors (Recovery-Focused):**
```css
--primary: Calming blue (221.2 83.2% 53.3%)
--destructive: Soft red (0 84.2% 60.2%) /* Not alarming */
--success: Gentle green (142.1 76.2% 36.3%)
```

**Accessibility:**
- WCAG AAA compliance (7:1 contrast ratio)
- Visible focus rings (3px, high contrast)
- Screen reader optimized

### Component Usage

```tsx
import { Button } from '@/src/components/ui/button';
import { Input } from '@/src/components/ui/input';
import { FormField } from '@/src/components/forms/FormField';

<FormField
  label="Email address"
  hint="We'll never share this"
  error={errors.email}
  required
>
  <Input type="email" />
</FormField>

<Button variant="default" size="lg">
  Submit Application
</Button>
```

See [Component Library Guide](docs/component-library.md) for all components.

---

## Testing

### Unit/Component Tests (Jest)

```bash
npm test                 # Run all tests
npm test -- Button       # Run specific test file
npm run test:coverage    # Generate coverage report
```

**Coverage Requirements:** 85% minimum (branches, functions, lines, statements)

**Example:**
```typescript
it('shows supportive error message', () => {
  render(
    <FormField error="Let's try that again">
      <Input />
    </FormField>
  );
  expect(screen.getByText(/let's try that again/i)).toBeInTheDocument();
});
```

### E2E Tests (Playwright)

```bash
npm run test:e2e         # Run E2E tests
npm run test:e2e:ui      # Run with UI (debugging)
```

**Browsers:** Chrome, Firefox, Safari (in CI)

**Example:**
```typescript
test('can submit login form', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

See [Testing Guide](docs/testing-guide.md) for comprehensive patterns.

---

## Observability

### HIPAA-Compliant Logging

**Never log PII/PHI.** Use the custom logger with allowlist-based redaction:

```typescript
import { logger } from '@/src/lib/logger';

// Safe: only logs userId, statusCode, timestamp
logger.info('User action', {
  userId: 'user-123',
  email: 'user@example.com',  // Silently dropped
  statusCode: 200,
});

// Track user interactions
logger.logUserAction('click', 'SubmitButton', {
  duration: 150,
});

// Track API calls (strips query params)
logger.logApiCall('POST', '/api/profile', 200, 250);
```

**Safe Fields (Allowlist):**
- `userId` (truncated to `uuid-XXXXXXXX`)
- `timestamp`, `eventType`, `statusCode`, `errorCode`
- `component`, `action`, `duration`, `count`

**Everything else is silently dropped.**

### Error Tracking (Sentry)

Sentry automatically captures errors with PHI redaction:
- Email → `[EMAIL]`
- Phone → `[PHONE]`
- SSN → `[SSN]`
- Query params stripped from URLs
- User context removed

### Performance Monitoring (Web Vitals)

Tracked automatically via `<WebVitals />` component in `app/layout.tsx`:
- **LCP** (Largest Contentful Paint) - Target: < 2.5s
- **FID** (First Input Delay) - Target: < 100ms
- **CLS** (Cumulative Layout Shift) - Target: < 0.1
- **TTFB** (Time to First Byte) - Target: < 800ms
- **FCP** (First Contentful Paint) - Target: < 1.8s
- **INP** (Interaction to Next Paint) - Target: < 200ms

See [Observability Guide](docs/observability.md) for complete details.

---

## CI/CD

### GitHub Actions Workflows

**[`.github/workflows/warp-frontend-test.yml`](../../.github/workflows/warp-frontend-test.yml)**

**Triggers:**
- Every push to `main`
- Every PR touching `services/warp-frontend/**`

**Jobs:**
1. **Unit Tests** - Run Jest with coverage, fail if < 85%
2. **E2E Tests** - Run Playwright on Chrome, Firefox, Safari

**Artifacts:**
- Coverage report (uploaded on success)
- Playwright report (uploaded on failure)

---

## Phase 1 Deliverables ✅

All Phase 1 tasks complete:

- ✅ **[#343] Firebase Hosting Spike** - Validated SSR + Secret Manager
- ✅ **[#344] Architecture Decision Records** - 5 ADRs documented
- ✅ **[#345] Component Library** - 23+ components, design tokens, forms
- ✅ **[#346] Testing Infrastructure** - Jest, Playwright, CI/CD
- ✅ **[#347] Observability Framework** - Sentry, logger, Web Vitals

---

## Next: Phase 2 - Authentication UI

**Planned Deliverables:**
- [ ] Login/Register forms using component library
- [ ] Supabase Auth integration
- [ ] Protected routes and middleware
- [ ] Auth error handling with observability
- [ ] E2E auth flow tests

---

## Resources

- **GitHub Issues:** https://github.com/employa-work/employa-web/issues
- **Epic #327:** https://github.com/employa-work/employa-web/issues/327
- **Next.js Docs:** https://nextjs.org/docs
- **shadcn/ui Docs:** https://ui.shadcn.com
- **Sentry Docs:** https://docs.sentry.io/platforms/javascript/guides/nextjs/
- **Playwright Docs:** https://playwright.dev/

---

## Contributing

See workspace-level [CLAUDE.md](../../CLAUDE.md) for development guidelines.

**Key Principles:**
- Recovery-focused design (calming, supportive, non-judgmental)
- WCAG AAA accessibility (elderly-friendly)
- HIPAA compliance (no PII/PHI in logs)
- 85% test coverage minimum
- Comprehensive documentation

---

## License

Proprietary - Employa.work
