#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "🧹 [Cleanup Script] Cleaning Lab Environment..."
echo "=================================================="

# 1. Kill any existing runner process
pkill -9 -f run_scrum.py 2>/dev/null || true
pkill -9 -f run_loop.py 2>/dev/null || true

# 2. Clean workspace target directory (preserve .git and .gitkeep)
if [ -d "workspace" ]; then
    echo "🗑️  Cleaning workspace/ directory (preserving .git and .gitkeep)..."
    find workspace -mindepth 1 -maxdepth 1 -not -name '.git' -not -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true
fi

# 3. Clean state directory (.evaluator and runtime state files)
if [ -d "state/.evaluator" ]; then
    echo "🗑️  Cleaning state/.evaluator buffer files..."
    rm -rf state/.evaluator/* 2>/dev/null || true
fi

echo "🗑️  Cleaning state runtime files..."
rm -f state/current_issues.md state/refinement_questions.md state/memo.md state/execution_tracker.json 2>/dev/null || true

# 4. Clean initiatives if --all flag is passed
if [[ "${1:-}" == "--all" ]]; then
    echo "🗑️  [--all flag detected] Purging state/initiatives generated files..."
    if [ -d "state/initiatives" ]; then
        find state/initiatives -mindepth 1 -maxdepth 1 -not -name '.git' -not -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true
    fi
fi

# 5. Clean temporary analysis files in root
rm -f repository_analysis.md 2>/dev/null || true

# 6. Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✨ [Cleanup Complete] Safe Environment Reset Finished!"
