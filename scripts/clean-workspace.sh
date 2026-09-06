#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 1. Load config.env if present
if [ -f "${BASE_DIR}/config.env" ]; then
    # shellcheck disable=SC1091
    source "${BASE_DIR}/config.env"
fi

WS_REL="${WORKSPACE_REL:-${TARGET_DIR:-workspace}}"
WS_DIR="${BASE_DIR}/${WS_REL}"
ROOT_WS_DIR="${BASE_DIR}/workspace"

echo "🧹 Cleaning workspace directory (${WS_DIR})..."

# Clean target project directory if exists
if [ -d "${WS_DIR}" ]; then
    find "${WS_DIR}" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ Target workspace (${WS_REL}) cleaned successfully!"
fi

# Clean parent workspace directory if different
if [ "${WS_DIR}" != "${ROOT_WS_DIR}" ] && [ -d "${ROOT_WS_DIR}" ]; then
    find "${ROOT_WS_DIR}" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ Root workspace directory cleaned successfully!"
fi

