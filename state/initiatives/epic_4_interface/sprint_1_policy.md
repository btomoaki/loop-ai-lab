```markdown
# Sprint Policy: Epic 4 — Sprint 1

## 1. Sprint Metadata
- **Epic:** Epic 4: HTTP Handlers, Server Entrypoint & Embedded SPA
- **Sprint:** 1
- **Task Name:** Implement HTTP REST Handlers, Security Headers Middleware, and Seed Validation
- **Target Files:**
  - `workspace/avatar-service/internal/infrastructure/handler/avatar_handler.go`
  - `workspace/avatar-service/internal/infrastructure/handler/avatar_handler_test.go`
- **Architectural Layer:** Infrastructure / Adapter Layer (`internal/infrastructure/handler`)
- **Go Module:** `avatar-service`

---

## 2. Objective & Scope
Construct the primary HTTP presentation layer for the `avatar-service` microservice. This includes:
1. REST endpoint `GET /api/avatar` for deterministic identicon generation and streaming.
2. Single Page Application (SPA) endpoint `GET /` for serving the embedded frontend (`static/index.html`).
3. Uniform HTTP security headers application across all responses.
4. Input validation and defaulting for the `seed` query parameter.
5. Cloud-native error isolation (5xx errors logged to `stderr`, quiet `stdout`).
6. Comprehensive `httptest` test suite covering normal operations, edge cases, and failure modes.

---

## 3. Technical Requirements & Implementation Policy

### 3.1 Dependencies & Clean Architecture Layering
- **Layer Location:** Strictly reside under package `handler` (`internal/infrastructure/handler`).
- **Dependencies:** Depend strictly on the application usecase interface `usecase.AvatarUseCase` and `embed.FS` for static assets.
- **Zero External Dependencies:** Use only standard Go library packages (`net/http`, `net/http/httptest`, `embed`, `io`, `strings`, `unicode/utf8`, `log`, `os`). Do not introduce third-party HTTP routers or frameworks.

### 3.2 Struct Definition & Constructor
```go
package handler

import (
    "embed"
    "net/http"
    "avatar-service/internal/application/usecase"
)

// AvatarHandler manages HTTP requests for avatar generation and SPA delivery.
type AvatarHandler struct {
    useCase  usecase.AvatarUseCase
    staticFS embed.FS
}

// NewAvatarHandler creates a new instance of AvatarHandler.
func NewAvatarHandler(useCase usecase.AvatarUseCase, staticFS embed.FS) *AvatarHandler {
    return &AvatarHandler{
        useCase:  useCase,
        staticFS: staticFS,
    }
}
```

### 3.3 Endpoint: `GET /api/avatar` (`HandleGetAvatar`)
- **Route:** `GET /api/avatar`
- **Parameter Extraction:** Extract query parameter `seed` (`r.URL.Query().Get("seed")`).
- **Defaulting Rules:**
  - If `seed` is missing, empty, or contains only whitespace (`strings.TrimSpace(seed) == ""`), fall back to the default seed value `"default"`.
- **Validation Rules:**
  - The maximum allowable seed length is **256 characters** (`len(seed) <= 256` or rune count).
  - If `seed` exceeds 256 characters, respond immediately with `HTTP 400 Bad Request` and body:
    `"seed parameter exceeds maximum length of 256 characters\n"`.
- **Usecase Invocation:**
  - Execute avatar generation through `AvatarUseCase.GenerateAvatar(r.Context(), seed)` (or `GenerateAvatar(seed)`).
- **Caching & Media Headers:**
  - `Content-Type: image/png`
  - `Cache-Control: public, max-age=86400`
- **Error Handling:**
  - If generation fails, respond with `HTTP 500 Internal Server Error` (`"failed to generate avatar\n"`).
  - Log error details to `os.Stderr` without leaking internal traces to HTTP clients.

### 3.4 Endpoint: `GET /` (`HandleIndex`)
- **Route:** `GET /`
- **Behavior:** Serve `static/index.html` from `staticFS` (`h.staticFS.ReadFile("static/index.html")` or `h.staticFS.Open`).
- **Headers:**
  - `Content-Type: text/html; charset=utf-8`
- **Error Handling:**
  - If the static file is missing or unreadable, respond with `HTTP 500 Internal Server Error` and log to `os.Stderr`.

### 3.5 Security Headers Specification
Apply the following standard HTTP security headers to all responses served by the handler:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## 4. Test Suite Requirements (`avatar_handler_test.go`)

### 4.1 Mocking Strategy
- Implement a mock `AvatarUseCase` (`mockAvatarUseCase`) satisfying the `usecase.AvatarUseCase` interface.
- Provide configurable behavior in the mock to simulate both successful PNG byte returns and synthetic errors for testing 500 scenarios.

### 4.2 Test Matrix & Coverage Targets
The test suite must use `net/http/httptest` and execute the following test scenarios:

| Test Case | Request Path / Params | Expected Status | Expected Headers / Body Verification |
| :--- | :--- | :--- | :--- |
| **Valid ASCII Seed** | `GET /api/avatar?seed=alice` | `200 OK` | `Content-Type: image/png`, `Cache-Control: public, max-age=86400`, security headers present, body matches mocked PNG bytes. |
| **Missing Seed** | `GET /api/avatar` | `200 OK` | Defaults to `"default"`, `200 OK`, `Content-Type: image/png`. |
| **Whitespace-only Seed** | `GET /api/avatar?seed=%20%20%20` | `200 OK` | Defaults to `"default"`, `200 OK`, `Content-Type: image/png`. |
| **Multibyte UTF-8 Seed** | `GET /api/avatar?seed=テストユーザー` | `200 OK` | Preserves UTF-8 characters, `200 OK`, `Content-Type: image/png`. |
| **Oversized Seed (>256 chars)**| `GET /api/avatar?seed=<257 'a's>` | `400 Bad Request` | Descriptive error message, `Content-Type: text/plain; charset=utf-8`. |
| **UseCase Failure** | `GET /api/avatar?seed=error_trigger` | `500 Internal Error` | Error response, security headers preserved. |
| **SPA Index Delivery** | `GET /` | `200 OK` | `Content-Type: text/html; charset=utf-8`, security headers, body matches embedded HTML. |
| **Security Headers Audit** | All endpoints | Any status | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` present on all responses. |

### 4.3 Execution Command
```bash
go test -v -race -cover ./internal/infrastructure/handler/...
```

---

## 5. Definition of Done (DoD)
- [ ] `internal/infrastructure/handler/avatar_handler.go` created and adheres to Clean Architecture.
- [ ] `internal/infrastructure/handler/avatar_handler_test.go` implemented with 100% test pass rate.
- [ ] No third-party router or external libraries imported.
- [ ] All exported types, constructors, and methods have standard Go doc comments.
- [ ] `go vet ./internal/infrastructure/handler/...` returns 0 issues.
- [ ] Test harness `sprint_1_harness.sh` executes with exit code `0`.
```
