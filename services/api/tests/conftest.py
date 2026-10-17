from __future__ import annotations

import os
from pathlib import Path

# Force test environment and explicitly isolated test database
os.environ["APP_ENV"] = "test"
TEST_DB_PATH = Path(__file__).resolve().parent / "test_isolated.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.core.config import settings
settings.app_env = 'test'
settings.database_url = TEST_DB_URL
settings.rate_limit_enabled = False

import pytest
from app.db.session import Base, engine
from app.db.seed import main as seed_main


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema and baseline demo fixtures exist before test suite runs."""
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    seed_main()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
