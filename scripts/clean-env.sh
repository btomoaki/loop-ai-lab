#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "🧹 [Cleanup Script] Cleaning Lab Environment..."
echo "=================================================="

# 0. Kill any background run_scrum processes
pkill -9 -f "run_scrum.py" 2>/dev/null || true

# 1. Clean workspace/avatar-service/ (preserve .git)
if [ -d "workspace/avatar-service" ]; then
    echo "🗑️  Cleaning workspace/avatar-service (preserving .git)..."
    find workspace/avatar-service/ -maxdepth 1 ! -name 'avatar-service' ! -name '.git' ! -name '.' -exec rm -rf {} +
fi

# 2. Clean state/ directory (preserve state/.gitkeep)
if [ -d "state" ]; then
    echo "🗑️  Resetting state/ generated artifacts..."
    rm -rf state/sprints/* state/current_issues.md state/memo.md state/progress.md 2>/dev/null || true
    if [ -d "state/.evaluator" ]; then
        echo "🗑️  Cleaning state/.evaluator buffer files..."
        rm -rf state/.evaluator/* 2>/dev/null || true
    fi
    touch state/.gitkeep
fi

# 3. Clean python cache
echo "🗑️  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✨ [Cleanup Complete] Environment is 100% clean and zero processes running!"
echo "=================================================="
