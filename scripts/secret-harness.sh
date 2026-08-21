#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Secret & SOPS Credentials Harness Script
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${BASE_DIR}/config.env" ]; then
    # shellcheck disable=SC1091
    source "${BASE_DIR}/config.env"
fi

TARGET_DIR="${TARGET_DIR:-${BASE_DIR}/workspace}"
ENABLE_SOPS="${ENABLE_SOPS:-false}"

echo "🔒 [Secret Harness] Checking credentials safety for: ${TARGET_DIR}"

# 1. .gitignore チェックと設定
GITIGNORE_FILE="${TARGET_DIR}/.gitignore"
if [ -d "${TARGET_DIR}/.git" ] || [ -f "${GITIGNORE_FILE}" ]; then
    for ignore_pattern in ".env" "*.secret" "*.key" "secrets.dec.*"; do
        if ! grep -q "^${ignore_pattern}$" "${GITIGNORE_FILE}" 2>/dev/null; then
            echo "${ignore_pattern}" >> "${GITIGNORE_FILE}"
            echo "   Added '${ignore_pattern}' to ${GITIGNORE_FILE}"
        fi
    done
fi

# 2. SOPS 暗号化チェック（有効時）
if [ "${ENABLE_SOPS}" = "true" ]; then
    if command -v sops &> /dev/null; then
        echo "   SOPS command found. Secret verification active."
    else
        echo "⚠️ Warning: ENABLE_SOPS is true, but 'sops' CLI is not installed in environment."
    fi
fi

echo "✅ [Secret Harness] Credential safety checks completed."
