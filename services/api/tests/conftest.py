from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# Database selection:
# If explicit DATABASE_URL is provided (e.g. by CI with PostgreSQL), respect it.
# Otherwise, fall back to isolated local SQLite database.
explicit_db_url = os.environ.get("DATABASE_URL", "").strip()


def validate_test_database_url(url: str) -> None:
    """Ensure tests never run against production or unapproved database targets."""
    if not url:
        return

    normalized = url.lower().replace('\\', '/')
    if "pgcb_portal.db" in normalized or "pgcb.db" in normalized:
        raise RuntimeError(
            f"SAFETY VIOLATION: Test suite cannot run against primary database file: {url}. "
            "Tests must never modify or connect to 'pgcb_portal.db'."
        )
    app_env = os.environ.get("APP_ENV", "").lower()
    if app_env in ("production", "staging"):
        raise RuntimeError(f"SAFETY VIOLATION: Cannot run test suite when APP_ENV={app_env}!")

    from sqlalchemy.engine import make_url
    try:
        parsed_url = make_url(url)
    except Exception as exc:
        raise RuntimeError(f"SAFETY VIOLATION: Invalid database URL format: {url}") from exc

    host = (parsed_url.host or "").lower()
    database = (parsed_url.database or "").lower()

    forbidden_hosts = ("pgcb.org.bd", "hostseba.com", "prod", "production")
    for f_host in forbidden_hosts:
        if f_host in host:
            raise RuntimeError(
                f"SAFETY VIOLATION: Test DATABASE_URL targets production infrastructure ({host}): {url}"
            )

    # For non-SQLite (e.g. PostgreSQL, MySQL): enforce strict host & database allowlist
    if not parsed_url.drivername.startswith("sqlite"):
        approved_hosts = {"localhost", "127.0.0.1", "postgres", "test-db", "ci", "host.docker.internal"}
        allow_external = os.environ.get("ALLOW_EXTERNAL_TEST_DB", "").lower() in ("1", "true", "yes")
        if host not in approved_hosts and not allow_external:
            raise RuntimeError(
                f"SAFETY VIOLATION: PostgreSQL test target host '{host}' is not in approved test host list "
                f"({sorted(approved_hosts)}). Set ALLOW_EXTERNAL_TEST_DB=1 to authorize explicit remote test host."
            )

        forbidden_db_keywords = ("prod", "production", "staging", "live")
        if any(keyword in database for keyword in forbidden_db_keywords):
            raise RuntimeError(
                f"SAFETY VIOLATION: Database name '{database}' contains forbidden keyword "
                f"({forbidden_db_keywords}). Tests must never target production or staging databases."
            )
        if database in ("pgcb_portal", "pgcb", "portal"):
            raise RuntimeError(
                f"SAFETY VIOLATION: Database name '{database}' is the primary application database name. "
                "Tests must never target the primary database directly."
            )

        approved_db_names = {"pgcb_test_db", "pgcb_test", "pgcb_portal_test"}
        approved_db_suffixes = ("_test", "_test_db")
        allow_disposable = os.environ.get("ALLOW_DISPOSABLE_TEST_DB", "").lower() in ("1", "true", "yes")

        is_approved_db = (
            database in approved_db_names
            or any(database.endswith(sfx) for sfx in approved_db_suffixes)
            or allow_disposable
        )
        if not is_approved_db:
            raise RuntimeError(
                f"SAFETY VIOLATION: Destructive test target database name '{database}' is not an authorized test database. "
                f"Must be one of {sorted(approved_db_names)}, end with {approved_db_suffixes}, "
                "or set ALLOW_DISPOSABLE_TEST_DB=1 to authorize."
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
        with engine.connect():
            pass

    engine.dispose()
    if IS_SQLITE and TEST_DB_PATH and TEST_DB_PATH.exists():
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
