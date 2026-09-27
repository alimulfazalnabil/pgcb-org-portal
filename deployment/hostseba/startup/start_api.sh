#!/usr/bin/env bash
# ==============================================================================
# HostSeba Production Startup Script — FastAPI Backend (services/api)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
API_DIR="${REPO_ROOT}/services/api"
VENV_DIR="${API_DIR}/.venv"

cd "${API_DIR}"

if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
fi

export APP_ENV="${APP_ENV:-production}"

echo "[1/3] Verifying production contract..."
python scripts/verify_production_contract.py --mode production

echo "[2/3] Running PostgreSQL Alembic migrations..."
alembic upgrade head

echo "[3/3] Starting Uvicorn ASGI server on 127.0.0.1:8000..."
exec uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --proxy-headers \
    --forwarded-allow-ips="127.0.0.1"
