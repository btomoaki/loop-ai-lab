# FILE: state/initiatives/epic_4_interface/sprint_1_harness.sh
```bash
#!/usr/bin/env bash
# ==============================================================================
# Epic 4: HTTP Handlers, Server Entrypoint & Embedded SPA
# Sprint 1: Implement HTTP REST Handlers, Security Headers Middleware, and Seed Validation
# Test Harness & Verification Script: sprint_1_harness.sh
# ==============================================================================

set -euo pipefail

# ANSI color codes for formatted terminal output
readonly COLOR_RESET="\033[0m"
readonly COLOR_GREEN="\033[1;32m"
readonly COLOR_RED="\033[1;31m"
readonly COLOR_YELLOW="\033[1;33m"
readonly COLOR_CYAN="\033[1;36m"
readonly COLOR_GRAY="\033[0;37m"

# Test counters
PASSED_CHECKS=0
FAILED_CHECKS=0
TOTAL_CHECKS=0

log_info() {
    echo -e "${COLOR_CYAN}[INFO]${COLOR_RESET} $1"
}

log_pass() {
    echo -e "${COLOR_GREEN}[PASS]${COLOR_RESET} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

log_fail() {
    echo -e "${COLOR_RED}[FAIL]${COLOR_RESET} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

print_header() {
    echo -e "\n${COLOR_CYAN}==============================================================================${COLOR_RESET}"
    echo -e "${COLOR_CYAN}  $1${COLOR_RESET}"
    echo -e "${COLOR_CYAN}==============================================================================${COLOR_RESET}"
}

# ------------------------------------------------------------------------------
# 1. Environment & Working Directory Resolution
# ------------------------------------------------------------------------------
print_header "Phase 1: Working Directory Resolution & Environment Setup"

PROJECT_ROOT=""
if [[ -f "go.mod" ]] && grep -q "module avatar-service" "go.mod"; then
    PROJECT_ROOT="$(pwd)"
elif [[ -d "workspace/avatar-service" ]] && [[ -f "workspace/avatar-service/go.mod" ]]; then
    PROJECT_ROOT="$(pwd)/workspace/avatar-service"
elif [[ -d "avatar-service" ]] && [[ -f "avatar-service/go.mod" ]]; then
    PROJECT_ROOT="$(pwd)/avatar-service"
elif [[ -f "../../go.mod" ]] && grep -q "module avatar-service" "../../go.mod"; then
    PROJECT_ROOT="$(cd ../.. && pwd)"
else
    # Fallback to parent searches
    CURRENT_DIR="$(pwd)"
    while [[ "$CURRENT_DIR" != "/" ]]; do
        if [[ -f "$CURRENT_DIR/go.mod" ]] && grep -q "module avatar-service" "$CURRENT_DIR/go.mod"; then
            PROJECT_ROOT="$CURRENT_DIR"
            break
        fi
        CURRENT_DIR="$(dirname "$CURRENT_DIR")"
    done
fi

if [[ -z "$PROJECT_ROOT" || ! -d "$PROJECT_ROOT" ]]; then
    echo -e "${COLOR_RED}[ERROR] Could not locate avatar-service project root containing go.mod.${COLOR_RESET}"
    exit 1
fi

log_info "Detected project root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# ------------------------------------------------------------------------------
# 2. Target Files Verification
# ------------------------------------------------------------------------------
print_header "Phase 2: Target File Existence & Path Verification"

TARGET_HANDLER_FILE="internal/infrastructure/handler/avatar_handler.go"
TARGET_TEST_FILE="internal/infrastructure/handler/avatar_handler_test.go"

if [[ -f "${TARGET_HANDLER_FILE}" ]]; then
    log_pass "Handler source file exists: ${TARGET_HANDLER_FILE}"
else
    log_fail "Missing handler source file: ${TARGET_HANDLER_FILE}"
fi

if [[ -f "${TARGET_TEST_FILE}" ]]; then
    log_pass "Handler test file exists: ${TARGET_TEST_FILE}"
else
    log_fail "Missing handler test file: ${TARGET_TEST_FILE}"
fi

# Exit early if files are missing
if [[ ${FAILED_CHECKS} -gt 0 ]]; then
    echo -e "\n${COLOR_RED}Pre-check failed: Required target files not found.${COLOR_RESET}"
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Architectural & Dependency Constraints Checks
# ------------------------------------------------------------------------------
print_header "Phase 3: Clean Architecture & Zero Third-Party Dependency Audit"

# Check package declaration
if grep -Eq "^package handler" "${TARGET_HANDLER_FILE}"; then
    log_pass "Package declared as 'package handler'"
else
    log_fail "Package declaration is not 'handler' in ${TARGET_HANDLER_FILE}"
fi

# Check for third-party imports in handler source
DISALLOWED_IMPORTS=$(grep -E '^\s*"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/' "${TARGET_HANDLER_FILE}" | grep -v "avatar-service" || true)
if [[ -z "${DISALLOWED_IMPORTS}" ]]; then
    log_pass "Zero external/third-party imports detected in ${TARGET_HANDLER_FILE}"
else
    log_fail "Found disallowed third-party imports in ${TARGET_HANDLER_FILE}:\n${DISALLOWED_IMPORTS}"
fi

# Check struct and constructor signatures
if grep -q "type AvatarHandler struct" "${TARGET_HANDLER_FILE}"; then
    log_pass "AvatarHandler struct definition found"
else
    log_fail "AvatarHandler struct definition missing in ${TARGET_HANDLER_FILE}"
fi

if grep -Eq "func NewAvatarHandler\(" "${TARGET_HANDLER_FILE}"; then
    log_pass "NewAvatarHandler constructor function found"
else
    log_fail "NewAvatarHandler constructor function missing in ${TARGET_HANDLER_FILE}"
fi

if grep -Eq "func \([^)]+\) HandleGetAvatar\(" "${TARGET_HANDLER_FILE}"; then
    log_pass "HandleGetAvatar method found"
else
    log_fail "HandleGetAvatar method missing in ${TARGET_HANDLER_FILE}"
fi

if grep -Eq "func \([^)]+\) HandleIndex\(" "${TARGET_HANDLER_FILE}"; then
    log_pass "HandleIndex method found"
else
    log_fail "HandleIndex method missing in ${TARGET_HANDLER_FILE}"
fi

# ------------------------------------------------------------------------------
# 4. Acceptance Criteria Static Pattern Analysis
# ------------------------------------------------------------------------------
print_header "Phase 4: Acceptance Criteria Static Code Verification"

# Verify security headers in handler
if grep -q "X-Content-Type-Options" "${TARGET_HANDLER_FILE}" && grep -q "nosniff" "${TARGET_HANDLER_FILE}"; then
    log_pass "Security header X-Content-Type-Options: nosniff present"
else
    log_fail "Missing X-Content-Type-Options header in ${TARGET_HANDLER_FILE}"
fi

if grep -q "X-Frame-Options" "${TARGET_HANDLER_FILE}" && grep -q "DENY" "${TARGET_HANDLER_FILE}"; then
    log_pass "Security header X-Frame-Options: DENY present"
else
    log_fail "Missing X-Frame-Options header in ${TARGET_HANDLER_FILE}"
fi

if grep -q "Content-Security-Policy" "${TARGET_HANDLER_FILE}"; then
    log_pass "Content-Security-Policy header configured"
else
    log_fail "Missing Content-Security-Policy header in ${TARGET_HANDLER_FILE}"
fi

# Verify media and caching headers
if grep -q "image/png" "${TARGET_HANDLER_FILE}"; then
    log_pass "Content-Type: image/png header configuration found"
else
    log_fail "Content-Type: image/png missing in ${TARGET_HANDLER_FILE}"
fi

if grep -q "max-age=86400" "${TARGET_HANDLER_FILE}"; then
    log_pass "Cache-Control: max-age=86400 header configuration found"
else
    log_fail "Cache-Control: max-age=86400 missing in ${TARGET_HANDLER_FILE}"
fi

# Verify seed defaulting and validation (<= 256 chars)
if grep -q "default" "${TARGET_HANDLER_FILE}"; then
    log_pass "Default seed fallback logic found"
else
    log_fail "Default seed fallback logic not found in ${TARGET_HANDLER_FILE}"
fi

if grep -q "256" "${TARGET_HANDLER_FILE}"; then
    log_pass "Seed length validation (256 chars limit) found"
else
    log_fail "Seed length limit (256) check missing in ${TARGET_HANDLER_FILE}"
fi

# ------------------------------------------------------------------------------
# 5. Go Compilation & Vet Checks
# ------------------------------------------------------------------------------
print_header "Phase 5: Go Vet & Source Code Validation"

log_info "Running go vet on ./internal/infrastructure/handler/..."
if go vet ./internal/infrastructure/handler/...; then
    log_pass "go vet passed with zero warnings/errors"
else
    log_fail "go vet reported issues in ./internal/infrastructure/handler/..."
fi

# ------------------------------------------------------------------------------
# 6. Unit & Integration Test Execution with Race Detection and Coverage
# ------------------------------------------------------------------------------
print_header "Phase 6: Automated Test Suite Execution (go test)"

COVERAGE_FILE="/tmp/avatar_handler_coverage.out"

log_info "Executing tests: go test -v -race -covermode=atomic -coverprofile=${COVERAGE_FILE} ./internal/infrastructure/handler/..."
if go test -v -race -covermode=atomic -coverprofile="${COVERAGE_FILE}" ./internal/infrastructure/handler/...; then
    log_pass "All handler unit and integration tests passed successfully"
else
    log_fail "Handler unit/integration tests failed"
fi

# Check coverage percentage
if [[ -f "${COVERAGE_FILE}" ]]; then
    COVERAGE_PCT=$(go tool cover -func="${COVERAGE_FILE}" | grep "total:" | awk '{print $3}' | tr -d '%')
    log_info "Handler test coverage: ${COVERAGE_PCT}%"
    
    # Require at least 85% coverage
    if (( $(echo "${COVERAGE_PCT} >= 85.0" | bc -l 2>/dev/null || echo "1") )); then
        log_pass "Test coverage satisfies minimum threshold (>= 85%): current ${COVERAGE_PCT}%"
    else
        log_warn "Test coverage is below recommended 85% threshold: current ${COVERAGE_PCT}%"
    fi
    rm -f "${COVERAGE_FILE}"
fi

# ------------------------------------------------------------------------------
# 7. Summary & Final Verdict
# ------------------------------------------------------------------------------
print_header "Phase 7: Test Harness Verification Summary"

echo -e "Total Checks Executed : ${TOTAL_CHECKS}"
echo -e "Passed Checks         : ${COLOR_GREEN}${PASSED_CHECKS}${COLOR_RESET}"
echo -e "Failed Checks         : ${COLOR_RED}${FAILED_CHECKS}${COLOR_RESET}"

if [[ ${FAILED_CHECKS} -eq 0 ]]; then
    echo -e "\n${COLOR_GREEN}==============================================================================${COLOR_RESET}"
    echo -e "${COLOR_GREEN}  ALL VERIFICATION CHECKS PASSED: Sprint 1 Acceptance Criteria Met!${COLOR_RESET}"
    echo -e "${COLOR_GREEN}==============================================================================${COLOR_RESET}"
    exit 0
else
    echo -e "\n${COLOR_RED}==============================================================================${COLOR_RESET}"
    echo -e "${COLOR_RED}  VERIFICATION FAILED: ${FAILED_CHECKS} check(s) did not pass.${COLOR_RESET}"
    echo -e "${COLOR_RED}==============================================================================${COLOR_RESET}"
    exit 1
fi
```

# FILE: state/initiatives/epic_4_interface/sprint_1_policy.md
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
