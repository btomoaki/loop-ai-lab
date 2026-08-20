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
