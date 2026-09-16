#!/usr/bin/env bash
set -euo pipefail

# Eドライブ (/mnt/e/llama/models) を最優先で探索
if [ -n "${MODEL_DIR:-}" ]; then
  : # 環境変数指定優先
elif [ -d "/mnt/e/llama/models" ]; then
  MODEL_DIR="/mnt/e/llama/models"
elif [ -d "/mnt/c/llama/models" ]; then
  MODEL_DIR="/mnt/c/llama/models"
else
  MODEL_DIR="/mnt/e/llama/models"
fi

MODEL_NAME="${1:-mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf}"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"
PORT=11435

if [ ! -f "${MODEL_PATH}" ]; then
  echo "❌ Error: Model not found at ${MODEL_PATH}" >&2
  echo "Available models in ${MODEL_DIR}:" >&2
  ls -lh "${MODEL_DIR}"/*.gguf 2>/dev/null || true
  exit 1
fi

# Determine llama-server command location
LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-$(which llama-server 2>/dev/null || echo "$HOME/llama.cpp/build/bin/llama-server")}"

if [ ! -x "${LLAMA_SERVER_BIN}" ]; then
  echo "⚠️ Warning: llama-server executable not found in PATH or $HOME/llama.cpp/build/bin/llama-server." >&2
  echo "Please build or install llama.cpp, or set LLAMA_SERVER_BIN." >&2
fi

echo "🚀 Starting llama-server on Linux..."
echo " - Model: ${MODEL_PATH}"
echo " - Port:  ${PORT}"
echo " - Binary: ${LLAMA_SERVER_BIN}"

# Add WSL CUDA driver paths if present
if [ -d "/usr/lib/wsl/lib" ]; then
  export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
fi

exec "${LLAMA_SERVER_BIN}" \
  -m "${MODEL_PATH}" \
  --port "${PORT}" \
  -c 32768 \
  -np 1 \
  -ngl 99 \
  --host 127.0.0.1
