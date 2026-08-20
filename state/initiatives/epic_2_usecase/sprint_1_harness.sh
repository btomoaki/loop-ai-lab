#!/usr/bin/env bash
# ==============================================================================
# Sprint 1 Test Harness: Avatar Generation UseCase and Domain Orchestration
# Epic: Epic 2: Application UseCase & Business Logic
# ==============================================================================
set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_header() {
    echo -e "\n${BOLD}==============================================================================${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${BOLD}==============================================================================${NC}"
}

# Resolve project root directory
locate_project_root() {
    local current_dir
    current_dir="$(pwd)"

    if [[ -f "${current_dir}/go.mod" ]] && [[ -d "${current_dir}/internal/application/usecase" || -d "${current_dir}/internal" ]]; then
        echo "${current_dir}"
        return 0
    fi

    if [[ -d "${current_dir}/workspace/avatar-service" ]] && [[ -f "${current_dir}/workspace/avatar-service/go.mod" ]]; then
        echo "${current_dir}/workspace/avatar-service"
        return 0
    fi

    if [[ -d "${current_dir}/avatar-service" ]] && [[ -f "${current_dir}/avatar-service/go.mod" ]]; then
        echo "${current_dir}/avatar-service"
        return 0
    fi

    local parent_dir
    parent_dir="$(dirname "${current_dir}")"
    while [[ "${parent_dir}" != "/" ]]; do
        if [[ -f "${parent_dir}/go.mod" ]] && grep -q "module avatar-service" "${parent_dir}/go.mod" 2>/dev/null; then
            echo "${parent_dir}"
            return 0
        fi
        parent_dir="$(dirname "${parent_dir}")"
    done

    echo "${current_dir}"
}

PROJECT_ROOT="$(locate_project_root)"
log_info "Target Project Root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# ------------------------------------------------------------------------------
# Check 1: Target Files Placement and Existence
# ------------------------------------------------------------------------------
print_header "Check 1: Target Files Placement & Directory Structure"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

REQUIRED_FILES=(
    "internal/application/usecase/avatar_usecase.go"
    "internal/application/usecase/avatar_usecase_test.go"
)

ALL_FILES_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${file}" ]]; then
        log_info "Found required file: ${file}"
    else
        log_fail "Missing required file: ${file}"
        ALL_FILES_EXIST=false
    fi
done

if [[ "${ALL_FILES_EXIST}" == "true" ]]; then
    log_pass "All required UseCase target files exist in 'internal/application/usecase/'."
else
    log_fail "Directory structure or target files do not meet DoD placement requirements."
fi

# ------------------------------------------------------------------------------
# Check 2: Go Clean Architecture Layer & Import Boundary Enforcement
# ------------------------------------------------------------------------------
print_header "Check 2: Clean Architecture Layer & Import Boundary Audit"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

USECASE_FILE="internal/application/usecase/avatar_usecase.go"
FORBIDDEN_IMPORTS_FOUND=false

if [[ -f "${USECASE_FILE}" ]]; then
    # Extract imports
    IMPORTS=$(go list -f '{{ join .Imports "\n" }}' ./internal/application/usecase 2>/dev/null || true)
    
    # Verify forbidden dependencies (Infrastructure, HTTP handlers, 3rd party modules)
    FORBIDDEN_PATTERNS=(
        "avatar-service/internal/infrastructure"
        "avatar-service/internal/interface"
        "avatar-service/cmd"
        "net/http"
        "github.com"
        "golang.org/x"
    )

    for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
        if echo "${IMPORTS}" | grep -q "${pattern}"; then
            log_fail "Architectural violation: Forbidden import '${pattern}' found in ${USECASE_FILE}"
            FORBIDDEN_IMPORTS_FOUND=true
        fi
    done

    # Verify allowed domain dependencies exist
    if echo "${IMPORTS}" | grep -q "avatar-service/internal/domain/model" && \
       echo "${IMPORTS}" | grep -q "avatar-service/internal/domain/repository"; then
        log_info "Verified valid domain imports: internal/domain/model, internal/domain/repository"
    else
        log_warn "Application layer should import internal/domain/model and internal/domain/repository"
    fi

    if [[ "${FORBIDDEN_IMPORTS_FOUND}" == "false" ]]; then
        log_pass "Clean Architecture compliance verified: zero infrastructure/third-party dependencies in UseCase."
    else
        log_fail "Import boundary rules violated in UseCase layer."
    fi
else
    log_fail "Cannot verify imports: ${USECASE_FILE} not found."
fi

# ------------------------------------------------------------------------------
# Check 3: Interface & Constructor Symbol Contract Verification
# ------------------------------------------------------------------------------
print_header "Check 3: Interface and Provider Constructor Signatures"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [[ -f "${USECASE_FILE}" ]]; then
    INTERFACE_OK=false
    CONSTRUCTOR_OK=false
    STRUCT_OK=false

    # Check AvatarUseCase interface definition
    if grep -E "type\s+AvatarUseCase\s+interface" "${USECASE_FILE}" > /dev/null && \
       grep -E "Generate\(.*string\)\s*\(\s*\[\]byte\s*,\s*error\s*\)" "${USECASE_FILE}" > /dev/null; then
        INTERFACE_OK=true
        log_info "Verified 'AvatarUseCase' interface with 'Generate(seed string) ([]byte, error)'"
    else
        log_fail "Interface 'AvatarUseCase' or method signature 'Generate(seed string) ([]byte, error)' not found"
    fi

    # Check private struct avatarUseCase
    if grep -E "type\s+avatarUseCase\s+struct" "${USECASE_FILE}" > /dev/null; then
        STRUCT_OK=true
        log_info "Verified private struct 'avatarUseCase'"
    else
        log_fail "Private struct 'avatarUseCase' not defined in ${USECASE_FILE}"
    fi

    # Check constructor NewAvatarUseCase
    if grep -E "func\s+NewAvatarUseCase\s*\(.*renderer\s+repository\.AvatarRenderer.*\)\s+AvatarUseCase" "${USECASE_FILE}" > /dev/null; then
        CONSTRUCTOR_OK=true
        log_info "Verified constructor 'NewAvatarUseCase(renderer repository.AvatarRenderer) AvatarUseCase'"
    else
        log_fail "Constructor 'NewAvatarUseCase(renderer repository.AvatarRenderer) AvatarUseCase' not found"
    fi

    if [[ "${INTERFACE_OK}" == "true" && "${STRUCT_OK}" == "true" && "${CONSTRUCTOR_OK}" == "true" ]]; then
        log_pass "Interface contracts and constructor signatures strictly adhere to acceptance criteria."
    else
        log_fail "Symbol signature mismatch against specification."
    fi
else
    log_fail "Cannot verify signatures: ${USECASE_FILE} not found."
fi

# ------------------------------------------------------------------------------
# Check 4: Static Analysis (go vet)
# ------------------------------------------------------------------------------
print_header "Check 4: Static Analysis & Linter Verification"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if go vet ./internal/application/usecase/...; then
    log_pass "'go vet ./internal/application/usecase/...' passed with zero warnings."
else
    log_fail "'go vet ./internal/application/usecase/...' reported issues."
fi

# ------------------------------------------------------------------------------
# Check 5: Race Condition Detection & Unit Test Execution
# ------------------------------------------------------------------------------
print_header "Check 5: Unit Tests & Data Race Verification"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if go test -race -v ./internal/application/usecase/...; then
    log_pass "Unit test suite passed with zero failures and zero race conditions."
else
    log_fail "Unit tests failed or detected data race conditions."
fi

# ------------------------------------------------------------------------------
# Check 6: 100% Statement & Branch Coverage Verification
# ------------------------------------------------------------------------------
print_header "Check 6: 100% Statement and Branch Coverage Verification"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

COVERAGE_PROFILE="/tmp/usecase_coverage.out"
if go test -coverprofile="${COVERAGE_PROFILE}" -covermode=atomic ./internal/application/usecase/... > /dev/null 2>&1; then
    COVERAGE_PERCENT=$(go tool cover -func="${COVERAGE_PROFILE}" | grep "total:" | awk '{print $3}' | tr -d '%')
    log_info "Total UseCase Statement Coverage: ${COVERAGE_PERCENT}%"

    if (( $(echo "${COVERAGE_PERCENT} >= 100.0" | bc -l 2>/dev/null || [ "${COVERAGE_PERCENT}" = "100.0" ] && echo 1 || echo 0) )); then
        log_pass "Achieved 100.0% statement coverage in 'internal/application/usecase'."
    else
        log_fail "Coverage requirement not met: expected 100.0%, got ${COVERAGE_PERCENT}%."
    fi
    rm -f "${COVERAGE_PROFILE}"
else
    log_fail "Failed to generate test coverage profile."
fi

# ------------------------------------------------------------------------------
# Check 7: Test Vectors & Mocking Completeness Audit
# ------------------------------------------------------------------------------
print_header "Check 7: Test Vector & Edge Case Coverage Audit"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

TEST_FILE="internal/application/usecase/avatar_usecase_test.go"
if [[ -f "${TEST_FILE}" ]]; then
    VECTORS_OK=true
    
    # Check for mock implementation
    if grep -E "(mock|stub)Renderer|MockAvatarRenderer" "${TEST_FILE}" > /dev/null || grep -E "type\s+mock.*struct" "${TEST_FILE}" > /dev/null; then
        log_info "Verified mock renderer implementation in test suite."
    else
        log_fail "Mock implementation of 'repository.AvatarRenderer' not found in tests."
        VECTORS_OK=false
    fi

    # Check for error handling test
    if grep -E "(err|Error|render_error|failure)" "${TEST_FILE}" > /dev/null; then
        log_info "Verified error propagation test case."
    else
        log_fail "Error propagation test case not found."
        VECTORS_OK=false
    fi

    # Check for empty/multibyte/edge case tests
    if grep -E "(empty|whitespace|multibyte|Japanese|utf8|emoji|日本語)" "${TEST_FILE}" > /dev/null || \
       grep -E '("")|("   ")' "${TEST_FILE}" > /dev/null; then
        log_info "Verified edge case / multibyte test vectors."
    else
        log_warn "Explicit edge cases (empty string, whitespace, multibyte) should be documented in test cases."
    fi

    if [[ "${VECTORS_OK}" == "true" ]]; then
        log_pass "Test vectors and mock verification completed successfully."
    else
        log_fail "Test suite lacks required mock or scenario coverage."
    fi
else
    log_fail "Cannot verify test vectors: ${TEST_FILE} not found."
fi

# ------------------------------------------------------------------------------
# Summary & Exit
# ------------------------------------------------------------------------------
print_header "Harness Execution Summary"
echo -e "Total Checks : ${TOTAL_CHECKS}"
echo -e "Passed       : ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed       : ${RED}${FAILED_CHECKS}${NC}"

if [[ ${FAILED_CHECKS} -eq 0 ]]; then
    echo -e "\n${GREEN}${BOLD}✓ ALL QUALITY GATES PASSED (Sprint 1 DoD Satisfied)${NC}\n"
    exit 0
else
    echo -e "\n${RED}${BOLD}✗ HARNESS VERIFICATION FAILED (${FAILED_CHECKS} checks failed)${NC}\n"
    exit 1
fi
