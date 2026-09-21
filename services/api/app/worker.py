from __future__ import annotations

import os
import time
from app.db.session import SessionLocal
from app.domain.membership import queue_membership_reminders
from app.domain.notifications import process_due_deliveries
from app.domain.workflows import publish_scheduled_content

# Expose Celery application for Render worker
try:
    from celery import Celery
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    celery_app = Celery('pgcb_worker', broker=redis_url, backend=redis_url)
    celery_app.conf.broker_connection_retry_on_startup = True

    @celery_app.task(name='app.worker.process_jobs')
    def process_jobs() -> dict[str, int]:
        return run_once()

    @celery_app.task(name='app.worker.send_receipt_task')
    def send_receipt_task(transaction_id: str) -> dict[str, str]:
        print(f"Receipt task processed for transaction: {transaction_id}")
        return {'transaction_id': str(transaction_id), 'status': 'sent'}
except Exception:
    celery_app = None
    send_receipt_task = None


def run_once() -> dict[str, int]:
    db = SessionLocal()
    try:
        reminders = queue_membership_reminders(db)
        scheduled = publish_scheduled_content(db)
        db.commit()
        deliveries = process_due_deliveries(db, limit=100)
        return {'membership_events': reminders, 'scheduled_publications': scheduled, 'notification_deliveries': deliveries}
    finally:
        db.close()


def main() -> None:
    interval = int(os.getenv('WORKER_INTERVAL_SECONDS', '30'))
    while True:
        try:
            print(f'worker: {run_once()}', flush=True)
        except Exception as exc:
            print(f'worker error: {exc}', flush=True)
        time.sleep(max(5, interval))

if __name__ == '__main__':
    main()
