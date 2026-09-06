#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 1. Load config.env if present
if [ -f "${BASE_DIR}/config.env" ]; then
    # shellcheck disable=SC1091
    source "${BASE_DIR}/config.env"
fi

STATE_PATH="${BASE_DIR}/${STATE_DIR:-state}"
INITIATIVES_PATH="${BASE_DIR}/${INITIATIVES_DIR:-state/initiatives}"
EVALUATOR_PATH="${BASE_DIR}/${EVALUATOR_DIR:-state/.evaluator}"
STATUS_PATH="${BASE_DIR}/${STATUS_FILE:-state/status.md}"

echo "🚀 Starting full project initialization..."

# 2. Include and execute workspace cleanup
# shellcheck disable=SC1090
source "${SCRIPT_DIR}/clean-workspace.sh"

# 3. Clean initiatives directory
if [ -d "${INITIATIVES_PATH}" ]; then
    find "${INITIATIVES_PATH}" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ Initiatives directory (${INITIATIVES_PATH}) initialized successfully!"
fi

# 4. Clean backup initiatives if exists
if [ -d "${STATE_PATH}/initiatives_backup_local" ]; then
    rm -rf "${STATE_PATH}/initiatives_backup_local"
    echo "✅ Removed ${STATE_PATH}/initiatives_backup_local!"
fi

# 5. Clean evaluator directory
if [ -d "${EVALUATOR_PATH}" ]; then
    find "${EVALUATOR_PATH}" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ Evaluator directory (${EVALUATOR_PATH}) initialized successfully!"
fi

# 6. Reset status dashboard (status.md)
if [ -f "${STATUS_PATH}" ]; then
    rm -f "${STATUS_PATH}"
    echo "✅ Reset status dashboard (${STATUS_PATH})!"
fi

# 7. Clean state/ root orphan files & debug logs
if [ -d "${STATE_PATH}" ]; then
    find "${STATE_PATH}" -maxdepth 1 -type f ! -name ".gitkeep" -name "debug_*" -exec rm -f {} +
    rm -f "${STATE_PATH}/refinement_debate_log.md"
    echo "✅ State root orphan debug logs purged!"
fi

echo "✨ Project initialization complete! Ready for fresh refinement."
