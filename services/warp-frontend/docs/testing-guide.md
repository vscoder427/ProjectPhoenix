# Warp Frontend - Testing Guide

**Purpose:** Comprehensive testing strategy for warp-frontend with 85% coverage minimum.

**Tools:** Jest (unit/component), Playwright (E2E), React Testing Library

**Last Updated:** 2026-01-12

---

## Quick Start

```bash
# Run unit/component tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui
```

---

## Testing Stack

### Jest + React Testing Library (Unit/Component Tests)
- **Purpose:** Test components, hooks, utilities in isolation
- **Speed:** Fast (<10 seconds for full suite)
- **Coverage:** 85% minimum (enforced in CI)

### Playwright (E2E Tests)
- **Purpose:** Test complete user flows across pages
- **Speed:** Slower (~2 minutes)
- **Browsers:** Chrome, Firefox, Safari

---

## Test Structure

```
services/warp-frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx
│   │   │   └── button.test.tsx       # Component tests
│   │   └── forms/
│   │       ├── FormField.tsx
│   │       └── FormField.test.tsx
│   └── lib/
│       ├── utils.ts
│       └── utils.test.ts              # Utility tests
├── tests/
│   └── e2e/
│       └── homepage.spec.ts           # E2E tests
├── jest.config.js                     # Jest configuration
├── jest.setup.js                      # Jest setup (testing-library)
└── playwright.config.ts               # Playwright configuration
```

---

## Writing Component Tests

### Basic Component Test
```typescript
import { render, screen } from '@testing-library/react'
import { Button } from './button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })
})
```

### Testing User Interactions
```typescript
import userEvent from '@testing-library/user-event'

it('calls onClick when clicked', async () => {
  const user = userEvent.setup()
  const onClick = jest.fn()

  render(<Button onClick={onClick}>Click me</Button>)
  await user.click(screen.getByRole('button'))

  expect(onClick).toHaveBeenCalledTimes(1)
})
```

### Testing Form Inputs
```typescript
it('handles text input', async () => {
  const user = userEvent.setup()
  render(<Input />)

  const input = screen.getByRole('textbox')
  await user.type(input, 'test@example.com')

  expect(input).toHaveValue('test@example.com')
})
```

### Testing Accessibility
```typescript
it('sets aria-invalid on input when error', () => {
  render(
    <FormField error="Please enter valid email">
      <Input />
    </FormField>
  )
  expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
})
```

---

## Writing E2E Tests

### Basic Page Test
```typescript
import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Employa/);
});
```

### Testing Navigation
```typescript
test('can navigate to login page', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Sign in');
  await expect(page).toHaveURL('/login');
});
```

### Testing Form Submission
```typescript
test('can submit login form', async ({ page }) => {
  await page.goto('/login');

  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
});
```

---

## What to Test

### ✅ Unit Tests (Jest)
- **Utility functions:** `formatDate()`, `validateEmail()`, `cn()`
- **React hooks:** `useAuth()`, `useFormState()`
- **Simple components:** Button, Input, Label
- **Component logic:** Conditional rendering, prop handling

### ✅ Component Tests (Jest + RTL)
- **User interactions:** Clicks, typing, form submissions
- **Accessibility:** ARIA attributes, keyboard navigation, focus management
- **Edge cases:** Loading states, error states, empty states
- **Props:** Variant classes, disabled state, required fields

### ✅ E2E Tests (Playwright)
- **Critical user flows:** Login → Search → Apply
- **Multi-page navigation:** Homepage → Profile → Settings
- **Authentication:** Login, register, logout
- **Form workflows:** Complete form, validation, submission

### ❌ What NOT to Test
- **Third-party libraries:** Supabase, Zustand, TanStack Query (trust them)
- **Next.js internals:** Routing, SSR (trust Next.js)
- **Trivial code:** One-liners, getters/setters
- **CSS styling:** Unless critical to functionality

---

## Coverage Requirements

### Minimum: 85%
```javascript
// jest.config.js
coverageThreshold: {
  global: {
    branches: 85,
    functions: 85,
    lines: 85,
    statements: 85,
  },
}
```

**CI Enforcement:** GitHub Actions fails PR if coverage < 85%

### What Counts Toward Coverage
- ✅ `src/**/*.{ts,tsx}`
- ✅ `app/**/*.{ts,tsx}`
- ❌ `*.config.{ts,js}` (excluded)
- ❌ `*.stories.tsx` (excluded)
- ❌ `*.d.ts` (excluded)

---

## CI/CD Integration

### GitHub Actions Workflow
**File:** `.github/workflows/warp-frontend-test.yml`

**Triggers:**
- Every push to `main`
- Every pull request touching `services/warp-frontend/**`

**Jobs:**
1. **Unit Tests:** Run Jest with coverage, fail if < 85%
2. **E2E Tests:** Run Playwright on Chrome, Firefox, Safari

**Artifacts:**
- Coverage report (uploaded on success)
- Playwright report (uploaded on failure)

### Local Pre-Commit Hook (Optional)
```bash
# .git/hooks/pre-commit
#!/bin/sh
cd services/warp-frontend
npm test -- --bail --findRelatedTests $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$')
```

---

## Testing Patterns

### Recovery-Focused Error Messages
```typescript
it('shows supportive error message', () => {
  render(
    <Alert variant="error">
      <AlertTitle>Let's try that again</AlertTitle>
      <AlertDescription>
        Your email or password didn't match. Please check and try again.
      </AlertDescription>
    </Alert>
  )

  // ❌ Don't expect: "Error!", "Invalid credentials"
  // ✅ Do expect: "Let's try that again", supportive language
  expect(screen.getByText(/let's try that again/i)).toBeInTheDocument()
})
```

### Testing Accessibility (WCAG)
```typescript
it('has sufficient color contrast', () => {
  const { container } = render(<Button>Click me</Button>)
  const button = container.querySelector('button')

  // Check computed styles
  const styles = window.getComputedStyle(button!)
  const bgColor = styles.backgroundColor
  const textColor = styles.color

  // Calculate contrast ratio (helper function)
  const contrast = calculateContrast(bgColor, textColor)
  expect(contrast).toBeGreaterThanOrEqual(7) // WCAG AAA
})
```

### Testing Keyboard Navigation
```typescript
it('is keyboard accessible', async () => {
  const user = userEvent.setup()
  render(<Button>Click me</Button>)

  const button = screen.getByRole('button')
  button.focus()
  expect(button).toHaveFocus()

  await user.keyboard('{Enter}')
  // Assert expected behavior
})
```

---

## Mocking

### Mocking API Calls
```typescript
// Use MSW (Mock Service Worker)
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/jobs', (req, res, ctx) => {
    return res(ctx.json([{ id: 1, title: 'Software Engineer' }]))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### Mocking Next.js Router
```typescript
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
  }),
  useSearchParams: () => new URLSearchParams(),
}))
```

---

## Debugging Tests

### Jest
```bash
# Run specific test file
npm test -- button.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="renders with correct text"

# Debug with Node inspector
node --inspect-brk node_modules/.bin/jest --runInBand
```

### Playwright
```bash
# Run with UI (interactive debugging)
npm run test:e2e:ui

# Run in headed mode (see browser)
npx playwright test --headed

# Debug specific test
npx playwright test --debug homepage.spec.ts
```

---

## Common Issues

### Issue: "Cannot find module '@/src/components/...'"
**Solution:** Check `tsconfig.json` has correct path mapping:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### Issue: "ReferenceError: TextEncoder is not defined"
**Solution:** Update `jest.setup.js`:
```javascript
import { TextEncoder, TextDecoder } from 'util'
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder
```

### Issue: E2E tests timeout
**Solution:** Increase timeout in `playwright.config.ts`:
```typescript
export default defineConfig({
  timeout: 30000, // 30 seconds
})
```

---

## Best Practices

### ✅ Do
1. **Test behavior, not implementation:** Test what user sees/does
2. **Use semantic queries:** `getByRole`, `getByLabelText` over `getByTestId`
3. **Write descriptive test names:** "shows error when email is invalid"
4. **Test accessibility:** ARIA attributes, keyboard navigation
5. **Mock external dependencies:** API calls, third-party services
6. **Keep tests fast:** Mock expensive operations
7. **Test recovery-focused UX:** Supportive error messages, calming language

### ❌ Don't
1. **Test implementation details:** Internal state, private methods
2. **Rely on fragile selectors:** Class names, complex CSS selectors
3. **Write huge test files:** Split into logical groups
4. **Skip accessibility tests:** WCAG compliance is critical
5. **Test third-party code:** Trust well-tested libraries
6. **Ignore flaky tests:** Fix them immediately

---

## Resources

- **Jest Docs:** https://jestjs.io/
- **React Testing Library:** https://testing-library.com/react
- **Playwright Docs:** https://playwright.dev/
- **Testing Best Practices:** https://kentcdodds.com/blog/common-mistakes-with-react-testing-library

---

## Next Steps

### Phase 1 (Current)
- [x] Configure Jest + RTL
- [x] Configure Playwright
- [x] Write sample component tests (Button, Input, FormField)
- [x] Write sample E2E test (homepage)
- [x] Set up CI with 85% coverage enforcement
- [ ] Expand test suite to cover all 23+ components

### Phase 2 (Auth UI)
- [ ] Write tests for login/register forms
- [ ] Test authentication flows (E2E)
- [ ] Test form validation (supportive error messages)
- [ ] Test accessibility (screen readers, keyboard nav)

### Phase 3 (Job Search UI)
- [ ] Write tests for job search components
- [ ] Test job application flows (E2E)
- [ ] Test recovery milestone UI
- [ ] Load testing (performance)
