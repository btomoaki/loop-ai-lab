#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Progress & Alignment Audit Harness Script
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${BASE_DIR}/config.env" ]; then
    # shellcheck disable=SC1091
    source "${BASE_DIR}/config.env"
fi

PROGRESS_FILE="${PROGRESS_FILE:-${BASE_DIR}/PROGRESS.md}"
REVIEW_INTERVAL="${REVIEW_INTERVAL:-10}"

echo "================================================================="
echo " 📊 [Progress Harness] Tracking & Review Inspection"
echo "   Progress File   : ${PROGRESS_FILE}"
echo "   Review Interval : Every ${REVIEW_INTERVAL} loops"
echo "================================================================="

if [ ! -f "${PROGRESS_FILE}" ]; then
    echo "⚠️ Warning: Progress file '${PROGRESS_FILE}' not found."
    exit 0
fi

# 1. 進捗のチェックボックス件数カウント
COMPLETED_TASKS=$(grep -c '^- \[x\]' "${PROGRESS_FILE}" || true)
TOTAL_TASKS=$(grep -c '^- \[\(x\| \)' "${PROGRESS_FILE}" || true)

echo "📈 Progress Summary: ${COMPLETED_TASKS} / ${TOTAL_TASKS} tasks completed."

# 2. 定期方向性監査 (Alignment Review) の判定フラグチェック
CURRENT_LOOP_COUNT="${LOOP_COUNT:-0}"
if [ "${CURRENT_LOOP_COUNT}" -gt 0 ] && [ $((CURRENT_LOOP_COUNT % REVIEW_INTERVAL)) -eq 0 ]; then
    echo "⚠️ [ALIGNMENT REVIEW REQUIRED] Current loop (${CURRENT_LOOP_COUNT}) reached review interval (${REVIEW_INTERVAL})."
    echo "   Triggering Alignment Auditor Agent (agents/alignment-auditor.md)..."
    exit 10 # 10: 特殊コード (方向性監査トリガー)
fi

echo "✅ [Progress Harness] Status check completed."
