"""
Synchronous Scheduled Job Runner for PGCB Portal (HostSeba Cron Compatible).
Replaces legacy Celery/Redis background workers with zero-dependency CLI execution.
"""
from __future__ import annotations

import argparse
import json
from app.db.session import SessionLocal
from app.domain.membership import queue_membership_reminders
from app.domain.notifications import process_due_deliveries
from app.domain.workflows import publish_scheduled_content


def run_once() -> dict[str, int]:
    """Execute one pass of scheduled membership reminders, CMS publications, and notification deliveries."""
    db = SessionLocal()
    try:
        reminders = queue_membership_reminders(db)
        scheduled = publish_scheduled_content(db)
        db.commit()
        deliveries = process_due_deliveries(db, limit=100)
        return {
            'membership_events': reminders,
            'scheduled_publications': scheduled,
            'notification_deliveries': deliveries,
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Run PGCB scheduled maintenance tasks once (via Cron).')
    parser.add_argument('--once', action='store_true', default=True, help='Execute a single pass and exit')
    parser.parse_args()
    result = run_once()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
