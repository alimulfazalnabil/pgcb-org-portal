#!/usr/bin/env bash
# ==============================================================================
# HostSeba Daily Backup + Restore Verification Script
# Backs up PostgreSQL database + member uploads and verifies archive integrity.
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

echo "[Backup] Running daily DB + document backup with restore verification..."
python scripts/backup_pgcb.py --verify-restore --retain-days "${BACKUP_RETAIN_DAYS:-30}"

# Optional external sync (e.g., rclone or scp to off-site storage if configured)
if [ -n "${EXTERNAL_BACKUP_TARGET:-}" ]; then
    echo "[Backup] Syncing backups to external target: ${EXTERNAL_BACKUP_TARGET}"
    rsync -az "${BACKUP_DIR:-./backups}/" "${EXTERNAL_BACKUP_TARGET}/"
fi

echo "[Backup] Completed successfully."
