#!/usr/bin/env bash
# ==============================================================================
# HostSeba Cron Job Runner — Replaces Celery/Redis Workers with Lightweight CLI
# Usage: ./run_cron_jobs.sh [notifications|expiry|reminders]
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

TASK="${1:-notifications}"

case "${TASK}" in
    notifications)
        python -c "from app.db.session import SessionLocal; from app.services.notification_service import NotificationService; db=SessionLocal(); print(NotificationService.process_pending_retries(db)); db.close()"
        ;;
    expiry)
        python -c "from app.db.session import SessionLocal; from app.services.membership_service import MembershipService; db=SessionLocal(); print(MembershipService.process_expirations(db)); db.close()"
        ;;
    reminders)
        python -c "from app.db.session import SessionLocal; from app.services.event_service import EventService; db=SessionLocal(); print(EventService.send_upcoming_reminders(db)); db.close()"
        ;;
    *)
        echo "Unknown cron task: ${TASK}" >&2
        exit 1
        ;;
esac
