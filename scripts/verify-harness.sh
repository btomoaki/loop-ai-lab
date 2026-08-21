#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${BASE_DIR}/config.env" ]; then
    source "${BASE_DIR}/config.env"
fi

TARGET_DIR="${TARGET_DIR:-${BASE_DIR}/workspace}"
VERIFY_COMMAND="${VERIFY_COMMAND:-cd ${TARGET_DIR} && go test ./...}"

if [ ! -d "${TARGET_DIR}" ]; then
    mkdir -p "${TARGET_DIR}"
fi

cd "${TARGET_DIR}"

# -----------------------------------------------------------------
# Smart Pre-Harness Guard: 空ワークスペースの事前検知 (TARGET_DIR内)
# -----------------------------------------------------------------
HAS_FILES=$(find . -maxdepth 3 -type f ! -name "README.md" ! -name "prompt_history.md" ! -path "*/.git/*" -print 2>/dev/null | head -n 1 || true)
if [ -z "$HAS_FILES" ]; then
    echo "ℹ️ [Harness Guard] Target workspace is currently empty (No implementation files found)."
    exit 1
fi

echo "================================================================="
echo " [Harness] Target Directory: ${TARGET_DIR}"
echo " [Harness] Verify Command : ${VERIFY_COMMAND}"
echo "================================================================="

# -----------------------------------------------------------------
# Auto-resolve Go third-party dependencies before testing
# -----------------------------------------------------------------
if [ -f "go.mod" ]; then
    echo "📦 Auto-tidying Go dependencies (go mod tidy)..."
    go mod tidy 2>&1 || true
fi

echo "🚀 Running verification command..."
set +e
LOG_OUTPUT=$(eval "${VERIFY_COMMAND}" 2>&1 | sed -E "s|${HOME}/\.local/share/[^/]+/installs/go/[^/]+/src/|<GOROOT>/|g" | sed -E "s|${BASE_DIR}/workspace/[^/]+/||g" | sed -E "s|${BASE_DIR}/||g")
EXIT_CODE=$?
set -e

echo "-----------------------------------------------------------------"
echo "${LOG_OUTPUT}"
echo "-----------------------------------------------------------------"

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ [SUCCESS] Verification passed (Exit Code: 0)"
    exit 0
else
    echo "❌ [FAILED] Verification command failed (Exit Code: ${EXIT_CODE})"
    exit ${EXIT_CODE}
fi
