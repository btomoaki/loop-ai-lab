[PER-EPIC HARNESS & POLICY GENERATION]
Generate an executable Bash test harness script (`sprint_1_harness.sh`) and policy (`sprint_1_policy.md`) for the following Sprint Backlog.

## SPRINT BACKLOG:
```yaml
Epic: "Epic 4: HTTP Handlers, Server Entrypoint & Embedded SPA"
Sprint: 1
TaskName: "Implement HTTP REST Handlers, Security Headers Middleware, and Seed Validation"
TargetFiles:
  - "workspace/avatar-service/internal/infrastructure/handler/avatar_handler.go"
  - "workspace/avatar-service/internal/infrastructure/handler/avatar_handler_test.go"
AcceptanceCriteria:
  - "Define AvatarHandler struct with dependencies on usecase.AvatarUseCase and embed.FS for static assets"
  - "Implement constructor NewAvatarHandler(useCase usecase.AvatarUseCase, staticFS embed.FS) *AvatarHandler"
  - "Implement HandleGetAvatar method (GET /api/avatar) extracting the 'seed' query parameter from request URL"
  - "Apply seed parameter defaulting: fallback to 'default' when 'seed' parameter is missing, empty, or whitespace-only"
  - "Enforce seed length validation: reject seeds exceeding 256 characters with HTTP 400 Bad Request and descriptive error message"
  - "Orchestrate avatar generation via AvatarUseCase and write binary PNG payload to http.ResponseWriter with HTTP 200 OK"
  - "Configure HTTP caching and media headers for GET /api/avatar: Content-Type: image/png, Cache-Control: public, max-age=86400"
  - "Configure standard security headers across endpoints: X-Content-Type-Options: nosniff, X-Frame-Options: DENY, and Content-Security-Policy: default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com"
  - "Implement HandleIndex method (GET /) to serve the embedded static/index.html with Content-Type: text/html; charset=utf-8"
  - "Handle usecase generation and rendering failures gracefully with HTTP 500 Internal Server Error"
  - "Implement comprehensive httptest suite in avatar_handler_test.go covering valid requests, default seeds, multibyte UTF-8 seeds, oversized seeds (400), security header verification, and internal error handling (500)"
DoD:
  - "All handler code strictly resides in internal/infrastructure/handler and adheres to Clean Architecture layer separation"
  - "Zero external dependencies: utilizes only Go standard library packages (net/http, net/http/httptest, embed, io)"
  - "All unit and integration tests in avatar_handler_test.go achieve 100% pass rate with high branch coverage"
  - "Exported symbols and constructor signatures are fully documented according to Go conventions"

```

CRITICAL INSTRUCTIONS:
Output the harness and policy files directly in the Epic directory:
1. `# FILE: state/initiatives/epic_4_interface/sprint_1_harness.sh` (Must start with `#!/usr/bin/env bash` and execute test checks)
2. `# FILE: state/initiatives/epic_4_interface/sprint_1_policy.md` (Implementation policy guidelines)
