#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${PWD}/backend/.uv-cache"

backend_pid=""

cleanup() {
  if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
    kill "${backend_pid}" 2>/dev/null || true
    wait "${backend_pid}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

(
  cd backend
  exec uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
backend_pid=$!

echo "Backend starting at http://127.0.0.1:8000"
echo "Frontend starting at http://localhost:3000"

pnpm --dir frontend dev
