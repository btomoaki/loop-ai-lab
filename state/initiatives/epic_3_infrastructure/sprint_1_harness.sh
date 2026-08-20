#!/usr/bin/env bash
# ==============================================================================
# Test Harness: Epic 3 - Sprint 1
# Task: Implement 250x250 PNG Image Rasterizer and Stream Encoder Adapter
# Target: internal/infrastructure/renderer/png_renderer.go
# ==============================================================================

set -euo pipefail

# ANSI Color Codes
readonly COLOR_RESET="\033[0m"
readonly COLOR_GREEN="\033[32m"
readonly COLOR_RED="\033[31m"
readonly COLOR_BLUE="\033[34m"
readonly COLOR_YELLOW="\033[33m"

log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $*"
}

log_pass() {
    echo -e "${COLOR_GREEN}[PASS]${COLOR_RESET} $*"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $*"
}

log_fail() {
    echo -e "${COLOR_RED}[FAIL]${COLOR_RESET} $*" >&2
}

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

if [[ -d "${PROJECT_ROOT}/workspace/avatar-service" ]]; then
    WORKDIR="${PROJECT_ROOT}/workspace/avatar-service"
elif [[ -f "${PROJECT_ROOT}/go.mod" ]]; then
    WORKDIR="${PROJECT_ROOT}"
else
    WORKDIR="$(pwd)"
fi

log_info "Executing Sprint 1 Test Harness in: ${WORKDIR}"
cd "${WORKDIR}"

# ------------------------------------------------------------------------------
# 1. Target Files Verification
# ------------------------------------------------------------------------------
log_info "Step 1: Verifying target files existence..."

TARGET_IMPL="internal/infrastructure/renderer/png_renderer.go"
TARGET_TEST="internal/infrastructure/renderer/png_renderer_test.go"

if [[ ! -f "${TARGET_IMPL}" ]]; then
    log_fail "Implementation file missing: ${TARGET_IMPL}"
    exit 1
fi

if [[ ! -f "${TARGET_TEST}" ]]; then
    log_fail "Test file missing: ${TARGET_TEST}"
    exit 1
fi
log_pass "Target files exist."

# ------------------------------------------------------------------------------
# 2. Dependency Audit (Strict Zero Third-Party Dependencies)
# ------------------------------------------------------------------------------
log_info "Step 2: Auditing dependencies for zero external package usage..."

EXTERNAL_IMPORTS=$(go list -f '{{range .Imports}}{{.}} {{end}}' ./internal/infrastructure/renderer/... 2>/dev/null | tr ' ' '\n' | grep -v '^$' | grep '\.' | grep -v 'avatar-service' || true)

if [[ -n "${EXTERNAL_IMPORTS}" ]]; then
    log_fail "Unauthorized external dependencies detected in renderer package:"
    echo "${EXTERNAL_IMPORTS}" >&2
    exit 1
fi
log_pass "Zero external dependencies verified (Standard Go library only)."

# ------------------------------------------------------------------------------
# 3. Source Formatting & Static Analysis
# ------------------------------------------------------------------------------
log_info "Step 3: Running gofmt and go vet..."

UNFORMATTED_FILES=$(gofmt -l internal/infrastructure/renderer/)
if [[ -n "${UNFORMATTED_FILES}" ]]; then
    log_fail "Code formatting issues detected by gofmt:"
    echo "${UNFORMATTED_FILES}" >&2
    exit 1
fi

if ! go vet ./internal/infrastructure/renderer/...; then
    log_fail "Static analysis failed with go vet."
    exit 1
fi
log_pass "Formatting and static analysis clean."

# ------------------------------------------------------------------------------
# 4. Unit Test Suite Execution & Coverage Verification
# ------------------------------------------------------------------------------
log_info "Step 4: Executing unit tests with race detector and coverage analysis..."

COVERAGE_FILE=$(mktemp)
trap 'rm -f "${COVERAGE_FILE}"' EXIT

if ! go test -v -race -covermode=atomic -coverprofile="${COVERAGE_FILE}" ./internal/infrastructure/renderer/...; then
    log_fail "Unit tests failed for ./internal/infrastructure/renderer/..."
    exit 1
fi

COVERAGE=$(go tool cover -func="${COVERAGE_FILE}" | grep 'total:' | awk '{print $3}' | tr -d '%')
log_info "Total renderer statement coverage: ${COVERAGE}%"

REQUIRED_COVERAGE="100.0"
if [[ "${COVERAGE}" != "${REQUIRED_COVERAGE}" ]]; then
    log_warn "Coverage is ${COVERAGE}%, expected ${REQUIRED_COVERAGE}%."
fi

# ------------------------------------------------------------------------------
# 5. Benchmark Performance Check
# ------------------------------------------------------------------------------
log_info "Step 5: Running rendering performance benchmarks..."
go test -run=^$ -bench=BenchmarkPNGRenderer ./internal/infrastructure/renderer/... -benchmem || true

log_pass "Sprint 1 Test Harness completed successfully."
exit 0
```

---
