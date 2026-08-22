#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WS_DIR="${BASE_DIR}/workspace"

echo "🧹 Cleaning workspace directory..."
if [ -d "${WS_DIR}" ]; then
    find "${WS_DIR}" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ Workspace cleaned successfully!"
else
    echo "⚠️ Workspace directory does not exist."
fi
