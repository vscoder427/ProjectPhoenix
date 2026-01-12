# ADR-0008: API Client Architecture

**Status:** Accepted
**Date:** 2026-01-12
**Deciders:** Damien (Product Owner), Claude (Technical Advisor)
**Issue:** [#328](https://github.com/employa-work/employa-web/issues/328)
**Epic:** [#328](https://github.com/employa-work/employa-web/issues/328) - Phase 2 Foundation

---

## Context

Warp-frontend needs to integrate with multiple backend APIs:
- **Dave API** (recovery chatbot, conversation history)
- **AAMeetings API** (meeting search, location-based queries)
- **CareerIntelligence API** (skills translation, recovery → career mapping)
- **n8n webhooks** (content generation, email workflows)

Current state:
- Ad-hoc API calls scattered across components using raw `fetch()`
- No centralized error handling
- No type safety (manual TypeScript interfaces)
- No contract testing (frontend-backend type mismatches possible)

Three key decisions needed:
1. **OpenAPI Strategy:** Contract-first with code generation vs manual clients?
2. **Client Structure:** How to organize API client code?
3. **Error Handling:** How to handle API errors consistently?

---

## Decision

**We will use OpenAPI contract-first development with feature-based client structure and hybrid error handling.**

### OpenAPI Contract-First Development
- **Dave & AAMeetings:** Export OpenAPI 3.1.0 specs to `docs/openapi/v1.yaml`
- **Type Generation:** Use `openapi-typescript-codegen` to generate TypeScript types
- **Contract Testing:** Use Schemathesis (Python) and Jest (TypeScript) to validate API contracts
- **Require OpenAPI 3.1.0** for all new APIs (ProjectPhoenix standard)
- **n8n webhooks:** Document payload schemas in TypeScript (no OpenAPI spec)

### Client Structure (Feature-Based)
```
Warp/src/lib/api/
├── client.ts              # Base HTTP client (retry, auth, logging)
├── types/                 # Generated OpenAPI types
│   ├── dave.ts           # Generated from Dave OpenAPI spec
│   ├── aaMeetings.ts     # Generated from AAMeetings OpenAPI spec
│   └── common.ts         # Shared types (ApiResponse, ApiError)
├── chat.ts               # Dave chat client (feature: chat)
├── meetings.ts           # AAMeetings client (feature: meetings)
├── jobs.ts               # Future: Job search API
├── profile.ts            # Future: Profile API
└── skills.ts             # Future: Skills translation API
```

### Error Handling (Hybrid)
- **Expected errors (return):** 404, 401, 403, 422 → Return `{ data: null, error: ApiError }`
- **Unexpected errors (throw):** 500, network errors → Throw exception (caught by error boundary)
- **Retry logic:** 3 retries with exponential backoff for 5xx errors

---

## Rationale

### OpenAPI Contract-First Development

**Why OpenAPI contract-first:**

**1. Type Safety**

**Without OpenAPI (manual types):**
```typescript
// Backend changes response shape
// Frontend doesn't know until runtime
interface ChatResponse {
  message: string;
  conversation_id: string;
  // Backend added 'metadata' field - frontend breaks
}
```

**With OpenAPI (generated types):**
```typescript
// Type generation fails if backend changes response
// Catch breaking changes at build time (not runtime)
import type { ChatResponse } from './types/dave';
// ChatResponse.metadata automatically available
```

**2. Contract Testing**

**Schemathesis (Backend):**
```bash
# Validates Dave API conforms to OpenAPI spec
schemathesis run http://localhost:8000/openapi.json --checks all
# Fails if: missing fields, wrong types, invalid status codes
```

**Jest (Frontend):**
```typescript
// Validates frontend expects what backend provides
it('should match OpenAPI spec for POST /chat', async () => {
  const response = await daveChatClient.sendMessage('Hello');
  expect(response.data).toHaveProperty('message');
  expect(response.data).toHaveProperty('conversation_id');
});
```

**3. Documentation**

OpenAPI spec serves as:
- **API documentation** (auto-generated docs at `/docs`)
- **Integration contract** (frontend-backend agreement)
- **Test fixtures** (generate mock data from schema)

**Why Dave and AAMeetings first:**

**Dave API:**
- ✅ FastAPI auto-generates OpenAPI 3.1.0 at `/docs` endpoint
- ✅ Most complex API (chat, conversation history, nudges, knowledge base)
- ✅ High integration priority (MVP feature)

**AAMeetings API:**
- ✅ FastAPI auto-generates OpenAPI 3.1.0 at `/docs` endpoint
- ✅ Simple API (search meetings by location)
- ✅ Good candidate for contract testing validation

**CareerIntelligence API:**
- ❓ Status unclear (may not exist yet, placeholder service)
- ⏸️ Defer until API is implemented

**n8n webhooks:**
- ❌ Not REST APIs (webhook payloads, no OpenAPI spec)
- ✅ Document payload schemas in TypeScript (manual types)

### Client Structure (Feature-Based)

**Why feature-based over service-based:**

**Service-Based Structure (Rejected):**
```
src/lib/api/
├── dave.ts                # All Dave endpoints
├── aaMeetings.ts          # All AAMeetings endpoints
└── careerIntelligence.ts  # All CareerIntelligence endpoints
```

**Problems:**
- ❌ Doesn't match frontend feature routes (from ADR-0002)
- ❌ Frontend features call multiple services (coupling)
- ❌ Hard to trace feature → API calls (debugging difficulty)

**Feature-Based Structure (Chosen):**
```
src/lib/api/
├── chat.ts        # Dave chat endpoints (feature: /chat route)
├── meetings.ts    # AAMeetings endpoints (feature: /meetings route)
├── jobs.ts        # Job search endpoints (feature: /jobs route)
└── profile.ts     # Profile endpoints (feature: /profile route)
```

**Benefits:**
- ✅ Matches feature-based routing (ADR-0002)
- ✅ Clear feature → API mapping (debugging simplicity)
- ✅ Co-locate related API calls (chat feature uses Dave API)
- ✅ Easier to mock for testing (mock chat.ts, not dave.ts)

**Example: Chat Feature**
```typescript
// Warp/src/lib/api/chat.ts
import { daveClient } from './client';
import type { ChatRequest, ChatResponse } from './types/dave';

export class DaveChatClient {
  async sendMessage(message: string, conversationId?: string) {
    return daveClient.post<ChatResponse>('/api/v1/chat', {
      message,
      conversation_id: conversationId,
    });
  }

  async getConversation(conversationId: string) {
    return daveClient.get<Conversation>(
      `/api/v1/conversations/${conversationId}`
    );
  }
}

export const daveChatClient = new DaveChatClient();
```

**Usage in component:**
```typescript
// Warp/src/app/chat/page.tsx
import { daveChatClient } from '@/lib/api/chat';

const result = await daveChatClient.sendMessage('Hello Dave');
if (result.error) {
  // Handle expected errors (404, 401)
  console.error(result.error.message);
} else {
  // Use typed response
  console.log(result.data.message);
}
```

### Error Handling (Hybrid)

**Why hybrid (return expected, throw unexpected):**

**Expected Errors (Return):**

```typescript
// 404 Not Found - user might search for non-existent meeting
const result = await aaMeetingsClient.getMeeting('invalid-id');
if (result.error?.status === 404) {
  return <div>Meeting not found</div>;
}

// 401 Unauthorized - session expired
const result = await daveChatClient.sendMessage('Hello');
if (result.error?.status === 401) {
  redirect('/auth/signin?error=SessionExpired');
}
```

**Benefits:**
- ✅ Explicit error handling (forces developer to check `result.error`)
- ✅ Type-safe errors (TypeScript enforces error checking)
- ✅ No try/catch boilerplate for common errors

**Unexpected Errors (Throw):**

```typescript
// 500 Internal Server Error - backend bug
try {
  await daveChatClient.sendMessage('Hello');
} catch (error) {
  // Caught by global error boundary
  // Logged to Sentry with context
  // User sees "Something went wrong" message
}
```

**Benefits:**
- ✅ Centralized error handling (error boundary)
- ✅ Automatic Sentry logging (no manual instrumentation)
- ✅ Fail fast (don't continue with invalid state)

**Error Classification:**

| Status Code | Error Type | Handling | Rationale |
|-------------|-----------|----------|-----------|
| 404 Not Found | Expected | Return | User might search for non-existent resource |
| 401 Unauthorized | Expected | Return | Session expired (redirect to login) |
| 403 Forbidden | Expected | Return | Insufficient permissions (show permission error) |
| 422 Validation Error | Expected | Return | Invalid input (show validation errors) |
| 500 Server Error | Unexpected | Throw | Backend bug (log to Sentry, show generic error) |
| Network error | Unexpected | Throw | Connection issue (log to Sentry, retry) |
| Parse error | Unexpected | Throw | Invalid JSON (log to Sentry, backend bug) |

---

## Alternatives Considered

### Option 1: Manual TypeScript Interfaces ❌

**Pros:**
- ✅ No build step (no code generation)
- ✅ Full control over types

**Cons:**
- ❌ Manual sync with backend (types can drift)
- ❌ No contract testing (breaking changes at runtime)
- ❌ Duplication (backend has types, frontend duplicates)
- ❌ Human error (typos, wrong types)

**Verdict:** Rejected due to lack of contract validation.

### Option 2: OpenAPI Contract-First ✅ **CHOSEN**

**Pros:**
- ✅ Type safety (generated from OpenAPI spec)
- ✅ Contract testing (catch breaking changes at build time)
- ✅ No duplication (single source of truth: OpenAPI spec)
- ✅ Auto-documentation (OpenAPI spec is documentation)
- ✅ Mock generation (generate mock data from schema)

**Cons:**
- ⚠️ Build step (type generation on `npm run dev`)
- ⚠️ Requires backend to export OpenAPI spec

**Verdict:** Best long-term solution (type safety, contract testing).

### Option 3: GraphQL Code Generation ❌

**Pros:**
- ✅ Type safety (generated from GraphQL schema)
- ✅ Contract testing (schema validation)
- ✅ Efficient queries (fetch only needed fields)

**Cons:**
- ❌ Backend rewrite (FastAPI → GraphQL)
- ❌ Different paradigm (REST → GraphQL)
- ❌ Overkill for MVP (simple CRUD operations)

**Verdict:** Rejected due to backend rewrite effort.

---

## Implementation

### Phase 1: Export OpenAPI Specs (Week 3, Days 1-2)

**Files to Modify:**

**Dave API:**
`Dave/api/app/main.py` (after line 50):

```python
import json
from pathlib import Path

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Export OpenAPI spec as JSON for client generation."""
    return app.openapi()

@app.on_event("startup")
async def export_openapi_spec():
    """Export OpenAPI spec to file on startup (dev only)."""
    if settings.environment == "development":
        openapi_schema = app.openapi()

        # Ensure docs/openapi directory exists
        spec_dir = Path(__file__).parent.parent.parent / "docs" / "openapi"
        spec_dir.mkdir(parents=True, exist_ok=True)

        # Write OpenAPI spec
        spec_path = spec_dir / "v1.yaml"
        with open(spec_path, "w") as f:
            import yaml
            yaml.dump(openapi_schema, f, sort_keys=False)

        logger.info(f"OpenAPI spec exported to {spec_path}")
```

**AAMeetings API:**
Same pattern as Dave API.

### Phase 2: Base HTTP Client (Week 3, Days 2-3)

**Files to Create:**

`Warp/src/lib/api/client.ts`:

```typescript
import { getSession } from 'next-auth/react';

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: unknown;
  correlationId: string;
}

export class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string, timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const session = await getSession();

    if (!session?.user) {
      return {};
    }

    const isAdmin = (session.user as any).is_admin;
    if (isAdmin) {
      return {
        'Authorization': `Bearer ${session.accessToken}`,
        'X-Admin-Role': (session.user as any).user_role,
      };
    }

    return {
      'Authorization': `Bearer ${session.accessToken}`,
    };
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, body);
  }

  async put<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, body);
  }

  async delete<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path);
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    retries: number = 3
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${path}`;
    const headers = await this.getAuthHeaders();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle expected errors (return as ApiError)
      if ([404, 401, 403, 422].includes(response.status)) {
        const errorData = await response.json().catch(() => ({}));
        return {
          data: null,
          error: {
            status: response.status,
            code: errorData.code || response.statusText,
            message: errorData.message || response.statusText,
            details: errorData,
            correlationId: response.headers.get('X-Trace-Id') || '',
          },
        };
      }

      // Handle server errors with retry logic
      if (response.status >= 500 && retries > 0) {
        await this.delay(Math.pow(2, 4 - retries) * 1000);
        return this.request<T>(method, path, body, retries - 1);
      }

      // Throw unexpected errors
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { data, error: null };

    } catch (error) {
      console.error('[API Client] Request failed:', {
        method,
        path,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      throw error;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton clients
export const daveClient = new ApiClient(
  process.env.NEXT_PUBLIC_DAVE_API_URL || 'http://localhost:8000'
);

export const aaMeetingsClient = new ApiClient(
  process.env.NEXT_PUBLIC_AAMEETINGS_API_URL || 'http://localhost:8001'
);
```

### Phase 3: Type Generation (Week 3, Day 3)

**Files to Create:**

`Warp/scripts/generate-api-types.ts`:

```typescript
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const SPECS = [
  {
    name: 'dave',
    url: 'http://localhost:8000/openapi.json',
    output: 'src/lib/api/types/dave.ts',
  },
  {
    name: 'aameetings',
    url: 'http://localhost:8001/openapi.json',
    output: 'src/lib/api/types/aameetings.ts',
  },
];

async function generateTypes() {
  for (const spec of SPECS) {
    console.log(`Generating types for ${spec.name}...`);

    const response = await fetch(spec.url);
    const openapi = await response.json();

    const tempPath = path.join(__dirname, `../temp-${spec.name}-openapi.json`);
    fs.writeFileSync(tempPath, JSON.stringify(openapi, null, 2));

    execSync(
      `npx openapi-typescript ${tempPath} --output ${spec.output}`,
      { stdio: 'inherit' }
    );

    fs.unlinkSync(tempPath);

    console.log(`✅ Generated ${spec.output}`);
  }
}

generateTypes().catch(console.error);
```

**Files to Modify:**

`Warp/package.json`:

```json
{
  "scripts": {
    "generate:api-types": "tsx scripts/generate-api-types.ts",
    "prebuild": "npm run generate:api-types",
    "dev": "npm run generate:api-types && next dev"
  },
  "devDependencies": {
    "openapi-typescript": "^6.7.0",
    "tsx": "^4.7.0"
  }
}
```

### Phase 4: Feature-Based Clients (Week 3, Days 4-5)

**Files to Create:**

`Warp/src/lib/api/chat.ts`:

```typescript
import { daveClient } from './client';
import type { paths } from './types/dave';

type ChatRequest = paths['/api/v1/chat']['post']['requestBody']['content']['application/json'];
type ChatResponse = paths['/api/v1/chat']['post']['responses']['200']['content']['application/json'];
type Conversation = paths['/api/v1/conversations/{id}']['get']['responses']['200']['content']['application/json'];

export class DaveChatClient {
  async sendMessage(message: string, conversationId?: string) {
    return daveClient.post<ChatResponse>('/api/v1/chat', {
      message,
      conversation_id: conversationId,
    });
  }

  async getConversation(conversationId: string) {
    return daveClient.get<Conversation>(`/api/v1/conversations/${conversationId}`);
  }

  async listConversations(userId: string) {
    return daveClient.get<Conversation[]>(`/api/v1/conversations?user_id=${userId}`);
  }

  async deleteConversation(conversationId: string) {
    return daveClient.delete(`/api/v1/conversations/${conversationId}`);
  }
}

export const daveChatClient = new DaveChatClient();
```

`Warp/src/lib/api/meetings.ts`:

```typescript
import { aaMeetingsClient } from './client';
import type { paths } from './types/aameetings';

type MeetingSearchRequest = paths['/api/v1/meetings/search']['post']['requestBody']['content']['application/json'];
type Meeting = paths['/api/v1/meetings/search']['post']['responses']['200']['content']['application/json'][0];

export class AAMeetingsClient {
  async searchMeetings(params: MeetingSearchRequest) {
    return aaMeetingsClient.post<Meeting[]>('/api/v1/meetings/search', params);
  }

  async getMeeting(meetingId: string) {
    return aaMeetingsClient.get<Meeting>(`/api/v1/meetings/${meetingId}`);
  }
}

export const aaMeetingsClient = new AAMeetingsClient();
```

`Warp/src/lib/api/index.ts`:

```typescript
export { daveChatClient } from './chat';
export { aaMeetingsClient } from './meetings';
export type * from './types/dave';
export type * from './types/aameetings';
```

### Phase 5: Contract Tests (Week 4, Days 1-2)

**Files to Create:**

`Dave/.github/workflows/contract-tests.yml`:

```yaml
name: Contract Tests

on:
  pull_request:
    paths:
      - 'api/**'
      - 'docs/openapi/**'

jobs:
  schemathesis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start Dave service
        run: docker-compose up -d

      - name: Wait for service
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'

      - name: Run Schemathesis contract tests
        run: |
          pip install schemathesis
          schemathesis run http://localhost:8000/openapi.json \
            --checks all \
            --hypothesis-max-examples=50 \
            --hypothesis-deadline=5000 \
            --exitfirst

      - name: Stop service
        if: always()
        run: docker-compose down
```

`Warp/src/lib/api/__tests__/contract-dave.test.ts`:

```typescript
import { describe, it, expect } from '@jest/globals';
import { daveChatClient } from '../chat';

describe('Dave API Contract Tests', () => {
  it('should match OpenAPI spec for POST /chat', async () => {
    const response = await daveChatClient.sendMessage('Hello Dave');

    expect(response.data).toHaveProperty('message');
    expect(response.data).toHaveProperty('conversation_id');
    expect(response.data).toHaveProperty('metadata');

    if (response.data) {
      expect(typeof response.data.message).toBe('string');
      expect(typeof response.data.conversation_id).toBe('string');
    }
  });

  it('should return 401 for unauthenticated requests', async () => {
    const response = await daveChatClient.sendMessage('Test');

    if (response.error) {
      expect(response.error.status).toBe(401);
    }
  });
});
```

---

## Consequences

### Positive

1. **Type Safety:** Generated types from OpenAPI spec (catch breaking changes at build time)
2. **Contract Testing:** Schemathesis + Jest validate API contracts (prevent type mismatches)
3. **Feature Alignment:** Client structure matches frontend routes (from ADR-0002)
4. **Centralized Error Handling:** Base client handles retry, logging, auth injection
5. **Explicit Error Handling:** Expected errors returned (forces developer to check `error` field)
6. **Auto-Documentation:** OpenAPI spec serves as API documentation

### Negative

1. **Build Step:** Type generation on `npm run dev` (adds 5-10s to startup)
2. **Backend Dependency:** Requires backend to export OpenAPI spec
3. **Migration Effort:** Replace ad-hoc `fetch()` calls with typed clients (~1 week)

### Neutral

1. **Feature-Based Structure:** Matches ADR-0002, different from service-based pattern
2. **Hybrid Error Handling:** Some errors returned, some thrown (not pure functional style)
3. **Contract Testing:** Requires CI/CD setup (Schemathesis in Dave, Jest in Warp)

---

## Success Metrics

### Type Safety Targets
- **Zero runtime type errors:** 0 "undefined is not an object" errors from API responses
- **Build-time catch rate:** 100% of breaking backend changes caught at build time

### Contract Testing Targets
- **Schemathesis pass rate:** 100% of Dave API endpoints pass contract tests
- **Jest contract test coverage:** 100% of critical API flows tested

### Developer Experience Targets
- **Type generation speed:** <10s for `npm run generate:api-types`
- **IDE autocomplete:** 100% of API client methods have TypeScript autocomplete

### Testing Checklist
- [ ] OpenAPI types generated (dave.ts, aameetings.ts)
- [ ] ChatRequest type has autocomplete in IDE
- [ ] 404 errors returned (not thrown)
- [ ] 500 errors thrown after retries
- [ ] Schemathesis contract tests pass (Dave)
- [ ] Jest contract tests pass (Warp)

---

## References

- **Phase 2 Epic:** [#328](https://github.com/employa-work/employa-web/issues/328)
- **Decision Plan:** `.claude/plans/snuggly-baking-hamster.md`
- **ADR-0002:** Feature-based routing (alignment rationale)
- **Dave API:** `Dave/api/app/main.py`
- **AAMeetings API:** `AAMeetings/api/app/main.py`
- **OpenAPI Docs:** https://spec.openapis.org/oas/v3.1.0
- **openapi-typescript:** https://github.com/drwpow/openapi-typescript
- **Schemathesis:** https://schemathesis.readthedocs.io/

---

## Notes

- **CareerIntelligence API:** Deferred until API is implemented (status unclear)
- **n8n webhooks:** No OpenAPI spec (document payload schemas in TypeScript)
- **Type Generation:** Run on `npm run dev` and `npm run build` (auto-sync)
- **Contract Tests:** CI/CD runs Schemathesis on backend PRs (catch breaking changes)
- **Error Boundary:** Unexpected errors caught by Next.js error boundary (global handler)
- **Retry Logic:** 3 retries with exponential backoff for 5xx errors (resilience)
