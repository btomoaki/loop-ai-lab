#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Verification & Guardrail Harness Script (Functional Code Focus)
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 設定ファイルの読み込み
if [ -f "${BASE_DIR}/config.env" ]; then
    # shellcheck disable=SC1091
    source "${BASE_DIR}/config.env"
fi

TARGET_DIR="${TARGET_DIR:-${BASE_DIR}/workspace/sample-project}"
LOCAL_SETUP_DIR="${LOCAL_SETUP_DIR:-${BASE_DIR}/../local-setup}"
VERIFY_COMMAND="${VERIFY_COMMAND:-make test}"

echo "================================================================="
echo " [Harness] Target Directory: ${TARGET_DIR}"
echo " [Harness] Verify Command : ${VERIFY_COMMAND}"
echo "================================================================="

# local-setup インフラのヘルスチェックおよび自動起動
if [ -d "${LOCAL_SETUP_DIR}" ]; then
    if ! curl -s --connect-timeout 2 http://registry.localhost &> /dev/null; then
        echo "⚠️  [Infrastructure] Local registry/proxy is not running."
        echo "🚀 [Infrastructure] Auto-starting local-setup infrastructure..."
        (cd "${LOCAL_SETUP_DIR}" && docker compose up -d) || true
    else
        echo "ℹ️  [Infrastructure] Common proxy & registry (local-setup) is healthy."
    fi
fi

if [ ! -d "${TARGET_DIR}" ]; then
    echo "❌ Error: Target directory '${TARGET_DIR}' does not exist."
    exit 1
fi

cd "${TARGET_DIR}"

echo "🚀 Running verification command..."
set +e
LOG_OUTPUT=$(eval "${VERIFY_COMMAND}" 2>&1)
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
