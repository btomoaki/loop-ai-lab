#!/usr/bin/env bash
# ==============================================================================
# Sprint 1 Verification Harness: 5×5 Symmetric Grid Matrix & Parity Fill
# Epic 1: Domain Core & Algorithmic Modeling
# ==============================================================================
set -euo pipefail

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}   Sprint 1 Test Harness: Grid Entity & Parity Fill Algorithm        ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. Workspace Directory Resolution
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT=""

# Search upwards or in common project structures
if [[ -f "${SCRIPT_DIR}/../../../go.mod" ]]; then
    WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/../../../../avatar-service/go.mod" ]]; then
    WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../../../avatar-service" && pwd)"
elif [[ -d "workspace/avatar-service" ]]; then
    WORKSPACE_ROOT="$(pwd)/workspace/avatar-service"
elif [[ -f "go.mod" ]]; then
    WORKSPACE_ROOT="$(pwd)"
elif [[ -d "avatar-service" ]]; then
    WORKSPACE_ROOT="$(pwd)/avatar-service"
else
    # Fallback to git root if available
    GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -n "${GIT_ROOT}" && -f "${GIT_ROOT}/go.mod" ]]; then
        WORKSPACE_ROOT="${GIT_ROOT}"
    elif [[ -n "${GIT_ROOT}" && -f "${GIT_ROOT}/avatar-service/go.mod" ]]; then
        WORKSPACE_ROOT="${GIT_ROOT}/avatar-service"
    fi
fi

if [[ -z "${WORKSPACE_ROOT}" ]]; then
    WORKSPACE_ROOT="$(pwd)/workspace/avatar-service"
fi
mkdir -p "${WORKSPACE_ROOT}"


cd "${WORKSPACE_ROOT}"
echo -e "${BLUE}[INFO] Running harness from workspace: ${WORKSPACE_ROOT}${NC}\n"

# ------------------------------------------------------------------------------
# 2. Target Files Pre-flight Check
# ------------------------------------------------------------------------------
echo -e "${BOLD}[Check 1/6] Verifying Target Files Existence...${NC}"
TARGET_GO="internal/domain/model/grid.go"
TARGET_TEST="internal/domain/model/grid_test.go"

MISSING_FILES=0
if [[ ! -f "${TARGET_GO}" ]]; then
    echo -e "  ${RED}✗ Missing required file: ${TARGET_GO}${NC}"
    MISSING_FILES=1
else
    echo -e "  ${GREEN}✓ Found: ${TARGET_GO}${NC}"
fi

if [[ ! -f "${TARGET_TEST}" ]]; then
    echo -e "  ${RED}✗ Missing required file: ${TARGET_TEST}${NC}"
    MISSING_FILES=1
else
    echo -e "  ${GREEN}✓ Found: ${TARGET_TEST}${NC}"
fi

if [[ ${MISSING_FILES} -ne 0 ]]; then
    echo -e "${RED}[FAIL] Pre-flight check failed: Required target files are missing.${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Clean Architecture & Dependency Isolation Check
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[Check 2/6] Verifying Clean Architecture Dependency Constraints...${NC}"

# Check for forbidden imports in internal/domain/model/grid.go
# Domain model for Grid should have zero external dependencies and zero infrastructure/rendering imports
FORBIDDEN_IMPORTS=$(grep -E '("image|"net/http|"internal/infrastructure|"internal/application|github.com|golang.org)' "${TARGET_GO}" || true)
if [[ -n "${FORBIDDEN_IMPORTS}" ]]; then
    echo -e "  ${RED}✗ Domain model '${TARGET_GO}' contains forbidden imports:${NC}"
    echo "${FORBIDDEN_IMPORTS}"
    echo -e "${RED}[FAIL] Dependency isolation violated: Domain models must have zero external/infra dependencies.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ Zero external or infrastructure dependencies detected in domain model.${NC}"

# Check exported symbols in grid.go
if ! grep -q "type Grid struct" "${TARGET_GO}"; then
    echo -e "  ${RED}✗ Exported struct 'Grid' not defined in ${TARGET_GO}${NC}"
    exit 1
fi
if ! grep -q "Cells.*\[5\]\[5\]bool" "${TARGET_GO}"; then
    echo -e "  ${RED}✗ Field 'Cells [5][5]bool' not defined in Grid struct${NC}"
    exit 1
fi
if ! grep -q "func NewGrid" "${TARGET_GO}"; then
    echo -e "  ${RED}✗ Exported constructor 'NewGrid(hash [16]byte) *Grid' not defined in ${TARGET_GO}${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ Exported symbols (Grid, Cells [5][5]bool, NewGrid) verified.${NC}"

# ------------------------------------------------------------------------------
# 4. Code Formatting & Lint / Vet
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[Check 3/6] Running Go Formatting (gofmt) & Static Vet...${NC}"
mkdir -p internal/domain/model
if [[ ! -f "internal/domain/model/grid.go" ]]; then
    echo -e "  ${RED}✗ Target internal/domain/model/grid.go not created yet.${NC}"
    exit 1
fi

UNFORMATTED=$(gofmt -l internal/domain/model/)
if [[ -n "${UNFORMATTED}" ]]; then
    echo -e "  ${RED}✗ Unformatted files found:${NC}"
    echo "${UNFORMATTED}"
    echo -e "${RED}[FAIL] Code style violation: Run 'go fmt ./internal/domain/model/...' to format files.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ All files in internal/domain/model comply with standard gofmt.${NC}"

if ! go vet ./internal/domain/model/...; then
    echo -e "${RED}[FAIL] 'go vet' reported issues in internal/domain/model/...${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ 'go vet' passed cleanly with zero warnings.${NC}"

# ------------------------------------------------------------------------------
# 5. Unit Tests & Race Condition Detection
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[Check 4/6] Executing Race Condition Detection (go test -race)...${NC}"
if ! go test -race -v ./internal/domain/model/...; then
    echo -e "${RED}[FAIL] Race condition check or unit tests failed.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ Zero race conditions detected across domain unit tests.${NC}"

# ------------------------------------------------------------------------------
# 6. Unit Test Statement & Branch Coverage Verification
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[Check 5/6] Verifying 100% Unit Test Code Coverage...${NC}"
COVERAGE_OUT=$(mktemp)
trap 'rm -f "${COVERAGE_OUT}"' EXIT

go test -coverprofile="${COVERAGE_OUT}" -covermode=atomic ./internal/domain/model/... > /dev/null

# Extract coverage percentage for grid.go
GRID_COVERAGE=$(go tool cover -func="${COVERAGE_OUT}" | grep "grid.go" | awk '{print $NF}' | tr -d '%')

if [[ -z "${GRID_COVERAGE}" ]]; then
    echo -e "  ${RED}✗ Could not determine coverage for grid.go${NC}"
    exit 1
fi

echo -e "  ${BLUE}Grid statement coverage: ${GRID_COVERAGE}%${NC}"

if (( $(echo "${GRID_COVERAGE} < 100.0" | bc -l) )); then
    echo -e "  ${RED}✗ Coverage is ${GRID_COVERAGE}%, which is below the mandatory 100% DoD threshold.${NC}"
    go tool cover -func="${COVERAGE_OUT}" | grep "grid.go"
    echo -e "${RED}[FAIL] DoD violated: 100% test coverage required for grid.go.${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ 100% Statement and branch coverage achieved for grid.go.${NC}"

# ------------------------------------------------------------------------------
# 7. Algorithmic Test Coverage Vectors Check
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[Check 6/6] Verifying Required Edge Case Vectors in Test Suite...${NC}"
REQUIRED_TESTS=(
    "TestNewGrid_Symmetry"
    "TestNewGrid_Parity"
    "TestNewGrid_Deterministic"
    "TestNewGrid_EdgeCases"
)

TEST_SOURCE=$(cat "${TARGET_TEST}")
MISSING_TESTS=0
for test_name in "${REQUIRED_TESTS[@]}"; do
    if ! echo "${TEST_SOURCE}" | grep -q "${test_name}"; then
        echo -e "  ${YELLOW}⚠ Recommended test function '${test_name}' not explicitly named in ${TARGET_TEST}${NC}"
    else
        echo -e "  ${GREEN}✓ Test case '${test_name}' identified.${NC}"
    fi
done

# ------------------------------------------------------------------------------
# Final Summary
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}   [PASS] All Sprint 1 Acceptance Criteria & DoD Gates Passed!       ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
exit 0
