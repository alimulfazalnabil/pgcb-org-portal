from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# Database selection:
# If explicit DATABASE_URL is provided (e.g. by CI with PostgreSQL), respect it.
# Otherwise, fall back to isolated local SQLite database.
explicit_db_url = os.environ.get("DATABASE_URL", "").strip()


from app.db.safety import (
    parse_authorized_target,
    validate_test_database_url,
    assert_destructive_database_permitted,
    is_test_migration_active,
)


TEST_DB_PATH: Path | None = None
if explicit_db_url:
    validate_test_database_url(explicit_db_url)
    CHOSEN_DB_URL = explicit_db_url
    IS_SQLITE = CHOSEN_DB_URL.startswith("sqlite")
    if IS_SQLITE and CHOSEN_DB_URL.startswith("sqlite:///"):
        raw_path = CHOSEN_DB_URL.replace("sqlite:///", "", 1)
        TEST_DB_PATH = Path(raw_path).resolve()
else:
    TEST_DB_PATH = Path(__file__).resolve().parent / "test_isolated.db"
    CHOSEN_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"
    IS_SQLITE = True

os.environ["DATABASE_URL"] = CHOSEN_DB_URL

# Force test storage isolation into a dedicated temporary directory
_TEST_STORAGE_DIR = tempfile.TemporaryDirectory(prefix="pgcb_test_storage_")
TEST_STORAGE_PATH = Path(_TEST_STORAGE_DIR.name).resolve()
os.environ["STORAGE_ROOT"] = str(TEST_STORAGE_PATH)

from app.core.config import settings
settings.app_env = 'test'
settings.database_url = CHOSEN_DB_URL
settings.storage_root = str(TEST_STORAGE_PATH)
settings.rate_limit_enabled = False

import app.services
app.services.set_base_storage(TEST_STORAGE_PATH)
from app.storage import reset_storage, get_storage
reset_storage()

import pytest
import app.db.session
from app.db.session import Base
from app.db.seed import main as seed_main

engine = app.db.session.set_engine(CHOSEN_DB_URL)


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema, baseline demo fixtures, and isolated storage exist before test suite runs."""
    validate_test_database_url(str(engine.url))

    if not IS_SQLITE:
        try:
            with engine.connect():
                pass
        except Exception as exc:
            raise RuntimeError(
                f"FATAL: Explicit PostgreSQL test database connection failed ({engine.url}). "
                "Connection failures must remain failures; tests must never fall back to another database."
            ) from exc

    engine.dispose()
    if IS_SQLITE and TEST_DB_PATH and TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    # Validate before destructive schema creation
    validate_test_database_url(str(engine.url), app_env=settings.app_env)
    assert_destructive_database_permitted(str(engine.url), action_name="test_schema_create", app_env=settings.app_env)
    Base.metadata.create_all(bind=engine)

    # Validate before destructive data seeding
    validate_test_database_url(str(engine.url), app_env=settings.app_env)
    assert_destructive_database_permitted(str(engine.url), action_name="test_data_seed", app_env=settings.app_env)
    seed_main()

    # Pre-create standard storage subdirectories in isolated test storage
    for sub in ('public', 'members', 'cards', 'certificates', 'documents', 'member_documents'):
        (TEST_STORAGE_PATH / sub).mkdir(parents=True, exist_ok=True)
    get_storage(root_override=TEST_STORAGE_PATH).ensure_root_exists()

    yield

    engine.dispose()
    if IS_SQLITE and TEST_DB_PATH and TEST_DB_PATH.exists():
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
