#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
STATE_DIR="${BASE_DIR}/state"

echo "🚀 Starting full project initialization..."

# 1. Include and execute workspace cleanup
source "${SCRIPT_DIR}/clean-workspace.sh"

# 2. Clean state/initiatives
if [ -d "${STATE_DIR}/initiatives" ]; then
    find "${STATE_DIR}/initiatives" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ State initiatives initialized successfully!"
fi

# 3. Clean state/initiatives_backup_local if exists
if [ -d "${STATE_DIR}/initiatives_backup_local" ]; then
    rm -rf "${STATE_DIR}/initiatives_backup_local"
    echo "✅ Removed state/initiatives_backup_local!"
fi

# 4. Clean state/.evaluator past logs
if [ -d "${STATE_DIR}/.evaluator" ]; then
    find "${STATE_DIR}/.evaluator" -mindepth 1 -maxdepth 1 ! -name ".gitkeep" -exec rm -rf {} +
    echo "✅ State .evaluator logs initialized successfully!"
rm -f "${STATE_DIR}/refinement_debate_log.md"
fi

echo "✨ Project initialization complete! Ready for fresh refinement."
