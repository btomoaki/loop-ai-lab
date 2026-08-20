#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "🧹 [Cleanup Script] Cleaning Lab Environment..."
echo "=================================================="

# 1. Kill any existing runner process
pkill -9 -f run_scrum.py 2>/dev/null || true

# 2. Clean target workspace source files except .git
if [ -d "workspace/avatar-service" ]; then
    echo "🗑️  Cleaning workspace/avatar-service (preserving .git)..."
    find workspace/avatar-service -maxdepth 1 -not -name '.git' -not -name 'avatar-service' -exec rm -rf {} + 2>/dev/null || true
fi

# 3. Clean evaluator buffer files
if [ -d "state/.evaluator" ]; then
    echo "🗑️  Cleaning state/.evaluator buffer files..."
    rm -rf state/.evaluator/* 2>/dev/null || true
fi

# 4. Remove generated runtime logs & temporary files, BUT PRESERVE state/initiatives/ unless --all is passed
rm -f state/current_issues.md state/refinement_questions.md state/memo.md 2>/dev/null || true

if [[ "${1:-}" == "--all" ]]; then
    echo "🗑️  [--all flag detected] Purging state/initiatives generated files..."
    rm -rf state/sprints/* 2>/dev/null || true
fi

# 5. Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✨ [Cleanup Complete] Safe Environment Reset Finished!"
echo "=================================================="

# 6. Ensure no socket leak connected to local LLM on port 11435
fuser -k 11435/tcp 2>/dev/null || true
