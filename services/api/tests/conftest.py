from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# Force test environment and explicitly isolated test database
os.environ["APP_ENV"] = "test"
TEST_DB_PATH = Path(__file__).resolve().parent / "test_isolated.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["DATABASE_URL"] = TEST_DB_URL

# Force test storage isolation into a dedicated temporary directory
_TEST_STORAGE_DIR = tempfile.TemporaryDirectory(prefix="pgcb_test_storage_")
TEST_STORAGE_PATH = Path(_TEST_STORAGE_DIR.name).resolve()
os.environ["STORAGE_ROOT"] = str(TEST_STORAGE_PATH)

from app.core.config import settings
settings.app_env = 'test'
settings.database_url = TEST_DB_URL
settings.storage_root = str(TEST_STORAGE_PATH)
settings.rate_limit_enabled = False

import app.services
app.services.set_base_storage(TEST_STORAGE_PATH)
from app.storage import reset_storage, get_storage
reset_storage()

import pytest
from app.db.session import Base, engine
from app.db.seed import main as seed_main


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema, baseline demo fixtures, and isolated storage exist before test suite runs."""
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    seed_main()

    # Pre-create standard storage subdirectories in isolated test storage
    for sub in ('public', 'members', 'cards', 'certificates', 'documents', 'member_documents'):
        (TEST_STORAGE_PATH / sub).mkdir(parents=True, exist_ok=True)
    get_storage(root_override=TEST_STORAGE_PATH).ensure_root_exists()

    yield

    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    # Clean up isolated test storage directory
    try:
        reset_storage()
        _TEST_STORAGE_DIR.cleanup()
    except Exception:
        pass
