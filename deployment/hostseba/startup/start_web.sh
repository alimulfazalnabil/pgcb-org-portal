#!/usr/bin/env bash
# ==============================================================================
# HostSeba Production Startup Script — Next.js Frontend (apps/web)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
WEB_DIR="${REPO_ROOT}/apps/web"

cd "${WEB_DIR}"

export NODE_ENV="production"
export INTERNAL_API_URL="${INTERNAL_API_URL:-http://127.0.0.1:8000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-/backend}"
export PORT="${PORT:-3000}"

if [ ! -d ".next" ]; then
    echo "Building Next.js production bundle..."
    npm ci
    npm run build
fi

echo "Starting Next.js server on 127.0.0.1:${PORT}..."
exec npm run start -- --hostname 127.0.0.1 --port "${PORT}"
