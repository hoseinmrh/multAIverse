#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${PWD}/backend/.uv-cache"

backend_host="${BACKEND_HOST:-127.0.0.1}"
backend_port="${BACKEND_PORT:-8000}"
frontend_host="${FRONTEND_HOST:-127.0.0.1}"
frontend_port="${FRONTEND_PORT:-3000}"
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
  exec uv run uvicorn app.main:app --reload --host "${backend_host}" --port "${backend_port}"
) &
backend_pid=$!

echo "Backend starting at http://${backend_host}:${backend_port}"
echo "Frontend starting at http://${frontend_host}:${frontend_port}"

pnpm --dir frontend exec next dev --hostname "${frontend_host}" --port "${frontend_port}"
