#!/usr/bin/env bash
# ==============================================================================
# HostSeba Administrative Restore Procedure
# Usage: ./restore_db_and_uploads.sh /path/to/pgcb-backup-YYYYMMDD-HHMMSS.tar.gz
# ==============================================================================
set -euo pipefail

ARCHIVE_PATH="${1:-}"
if [ -z "${ARCHIVE_PATH}" ] || [ ! -f "${ARCHIVE_PATH}" ]; then
    echo "Usage: $0 /path/to/pgcb-backup-YYYYMMDD-HHMMSS.tar.gz" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
API_DIR="${REPO_ROOT}/services/api"
VENV_DIR="${API_DIR}/.venv"

cd "${API_DIR}"
if [ -f "${VENV_DIR}/bin/activate" ]; then
    source "${VENV_DIR}/bin/activate"
fi

echo "[Restore] Step 1: Verifying backup archive integrity and SHA-256 manifest..."
python scripts/backup_pgcb.py --verify-archive "${ARCHIVE_PATH}"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

echo "[Restore] Step 2: Extracting archive to temporary staging directory..."
tar -xzf "${ARCHIVE_PATH}" -C "${WORK_DIR}"

if [ -f "${WORK_DIR}/database.pgdump" ] && [ -n "${DATABASE_URL:-}" ]; then
    PG_URL="${DATABASE_URL/+psycopg/}"
    echo "[Restore] Step 3: Restoring PostgreSQL database via pg_restore..."
    pg_restore --clean --if-exists --no-owner --dbname="${PG_URL}" "${WORK_DIR}/database.pgdump"
fi

if [ -d "${WORK_DIR}/uploads" ] && [ -n "${UPLOAD_DIR:-}" ]; then
    echo "[Restore] Step 4: Restoring persistent uploads directory to ${UPLOAD_DIR}..."
    mkdir -p "${UPLOAD_DIR}"
    cp -a "${WORK_DIR}/uploads/." "${UPLOAD_DIR}/"
fi

echo "[Restore] Restore completed and verified."
