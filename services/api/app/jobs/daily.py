"""Daily scheduled tasks executed via cron on Render."""
from __future__ import annotations

import logging
from app.worker import run_once

logger = logging.getLogger(__name__)

def main() -> None:
    print("[Cron] Starting PGCB daily scheduled tasks...", flush=True)
    try:
        results = run_once()
        print(f"[Cron] Daily tasks completed successfully: {results}", flush=True)
    except Exception as exc:
        print(f"[Cron] Error executing daily tasks: {exc}", flush=True)
        raise

if __name__ == '__main__':
    main()
