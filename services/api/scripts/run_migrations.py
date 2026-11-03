#!/usr/bin/env python3
"""
HostSeba / cPanel Database Migration Runner for PGCB Organization Portal.
Location: services/api/scripts/run_migrations.py

Designed specifically for manual cPanel deployments without SSH or Terminal access.
Can be executed directly via cPanel 'Setup Python App' -> 'Execute python script':
    scripts/run_migrations.py
Or from any shell / automated deployment runner:
    python scripts/run_migrations.py

Features:
- Programmatic Alembic execution (`alembic upgrade head`)
- Automatic virtualenv and sys.path configuration
- Credential masking in logs and console output
- Writes audit log to `services/api/migration_run.log`
"""
from __future__ import annotations

import logging
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

# 1. Ensure services/api is on sys.path
API_DIR = Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

try:
    os.chdir(API_DIR)
except Exception:
    pass

# 2. Setup logging to console and migration_run.log
LOG_FILE = API_DIR / "migration_run.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("run_migrations")


def mask_sensitive(text: str) -> str:
    """Mask database passwords, secret keys, tokens, and query credentials from strings."""
    if not text:
        return ""

    # 1. Mask standard URI credentials: ://user:password@host or ://:password@host
    text = re.sub(r"://([^/\s:@]+):([^/\s@]+)@", r"://\1:***@", text)
    text = re.sub(r"://:([^/\s@]+)@", r"://:***@", text)

    # 2. Mask query parameter secrets: ?token=xyz or &password=xyz
    text = re.sub(
        r"([?&](?:password|db_password|secret|key|token|auth_token|api_key|access_token)=)[^&\s]+",
        r"\1***",
        text,
        flags=re.IGNORECASE,
    )

    # 3. Mask key-value secrets: password=xyz or token: "xyz"
    text = re.sub(
        r"(password|db_password|secret|key|token|auth_token|api_key|access_token)\s*([=:])\s*([\"']?)([^\"'\s&,]+)\3",
        r"\1\2***",
        text,
        flags=re.IGNORECASE,
    )
    return text


def run_migrations() -> int:
    started_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info("=" * 60)
    logger.info("Starting PGCB Database Migration at %s", started_at)

    try:
        from alembic.config import Config
        from alembic import command
        from app.core.config import settings

        logger.info("Application Environment: %s", settings.app_env)
        masked_url = mask_sensitive(settings.database_url)
        logger.info("Target Database URL: %s", masked_url)

        # Fail-safe database check: SQLite is strictly prohibited in production and staging
        if settings.is_production_like and settings.database_url.lower().startswith("sqlite"):
            raise RuntimeError(
                "CRITICAL DEPLOYMENT ERROR: Staging and Production environments require a managed "
                "PostgreSQL database. Running migrations against SQLite in production or staging is strictly prohibited."
            )

        ini_path = API_DIR / "alembic.ini"
        if not ini_path.is_file():
            raise FileNotFoundError(f"Missing alembic.ini configuration file at: {ini_path}")

        alembic_cfg = Config(str(ini_path))
        alembic_cfg.set_main_option("script_location", str(API_DIR / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

        logger.info("Executing Alembic: upgrade head...")
        command.upgrade(alembic_cfg, "head")

        logger.info("[SUCCESS] Database schema is now at HEAD (latest revision).")
        logger.info("Migration completed successfully at %s", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
        logger.info("=" * 60)
        return 0

    except Exception as exc:
        raw_tb = traceback.format_exc()
        masked_tb = mask_sensitive(raw_tb)
        logger.error("[ERROR] Migration failed:\n%s", masked_tb)
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = run_migrations()
    sys.exit(exit_code)
