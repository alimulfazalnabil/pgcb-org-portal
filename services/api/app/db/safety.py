"""
Database Safety Verification Policy

Enforces fail-closed safety constraints for database connections, migrations,
test fixtures, and destructive operations (drop, create, synthetic seed, test reset).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote
from sqlalchemy.engine import make_url

# Standard environments where destructive actions (e.g. test wipe, local reset) are allowed
SAFE_DESTRUCTIVE_ENVIRONMENTS = frozenset({"test", "development", "dev", "local"})

# Forbidden infrastructure hosts that must never be targeted by tests or dev destructive actions
FORBIDDEN_HOSTS = frozenset({
    "pgcb.org.bd",
    "hostseba.com",
    "prod",
    "production",
})

# Forbidden database keywords that indicate production or staging data
FORBIDDEN_DB_KEYWORDS = ("prod", "production", "staging", "live")

# Primary application database names that tests must never target
PRIMARY_DB_NAMES = frozenset({"pgcb_portal", "pgcb", "portal"})

# Approved test hostnames for standard CI and local test containers
APPROVED_TEST_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "postgres",
    "test-db",
    "ci",
    "host.docker.internal",
})

# Approved test database names
APPROVED_TEST_DB_NAMES = frozenset({
    "pgcb_test_db",
    "pgcb_test",
    "pgcb_portal_test",
})

# Approved test database suffixes
APPROVED_TEST_DB_SUFFIXES = ("_test", "_test_db")


def mask_url_credentials(url: str) -> str:
    """Mask user credentials in database URLs to prevent credential leakage in error messages and logs."""
    if not url or not str(url).strip():
        return ""
    try:
        u = make_url(url)
        return u.render_as_string(hide_password=True)
    except Exception:
        # Regex fallback for malformed or unparseable URLs containing credentials
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', str(url))


def parse_authorized_target(target_str: str) -> tuple[str, int | None, str]:
    """
    Parse AUTHORIZED_TEST_DB_TARGET into (host, port, database).
    Accepts:
      - 'host/database' (e.g. '192.168.1.50/ephemeral_test')
      - 'host:port/database' (e.g. '192.168.1.50:5433/ephemeral_test')
      - '[ipv6]:port/database' (e.g. '[::1]:5432/ephemeral_test')
      - Full URL (e.g. 'postgresql://user:pass@host:5432/database')
    """
    target = (target_str or "").strip()
    if not target:
        raise ValueError("Empty authorization target. Specify 'host[:port]/database'.")

    if "://" in target:
        try:
            u = make_url(target)
            h = (u.host or "").lower().strip("[]")
            p = u.port
            d = unquote(u.database or "").lower()
            if not h or not d:
                raise ValueError()
            for f_host in FORBIDDEN_HOSTS:
                if f_host in h:
                    raise ValueError(f"Forbidden production infrastructure host '{h}' in AUTHORIZED_TEST_DB_TARGET")
            if any(keyword in d for keyword in FORBIDDEN_DB_KEYWORDS):
                raise ValueError(f"Database name '{d}' in AUTHORIZED_TEST_DB_TARGET contains forbidden keyword")
            if d in PRIMARY_DB_NAMES:
                raise ValueError(f"Database name '{d}' in AUTHORIZED_TEST_DB_TARGET is the primary database name")
            return h, p, d
        except Exception as exc:
            if isinstance(exc, ValueError) and ("Forbidden" in str(exc) or "forbidden" in str(exc) or "primary database" in str(exc)):
                raise
            raise ValueError(f"Malformed URL in AUTHORIZED_TEST_DB_TARGET: {mask_url_credentials(target)}") from exc

    if "/" not in target:
        raise ValueError(
            f"Malformed AUTHORIZED_TEST_DB_TARGET '{mask_url_credentials(target)}'. "
            "Must be in format 'host[:port]/database' or 'postgresql://...'"
        )

    try:
        u = make_url(f"dummy://{target}")
        h = (u.host or "").lower().strip("[]")
        p = u.port
        d = unquote(u.database or "").lower()
        if not h or not d:
            raise ValueError()
        for f_host in FORBIDDEN_HOSTS:
            if f_host in h:
                raise ValueError(f"Forbidden production infrastructure host '{h}' in AUTHORIZED_TEST_DB_TARGET")
        if any(keyword in d for keyword in FORBIDDEN_DB_KEYWORDS):
            raise ValueError(f"Database name '{d}' in AUTHORIZED_TEST_DB_TARGET contains forbidden keyword")
        if d in PRIMARY_DB_NAMES:
            raise ValueError(f"Database name '{d}' in AUTHORIZED_TEST_DB_TARGET is the primary database name")
        return h, p, d
    except Exception as exc:
        if isinstance(exc, ValueError) and ("Forbidden" in str(exc) or "forbidden" in str(exc) or "primary database" in str(exc)):
            raise
        raise ValueError(
            f"Malformed AUTHORIZED_TEST_DB_TARGET '{mask_url_credentials(target)}'. Expected 'host[:port]/database'."
        ) from exc


def validate_test_database_url(url: str, app_env: str | None = None) -> None:
    """Ensure tests never run against production or unapproved database targets."""
    if not url or not str(url).strip():
        raise RuntimeError("SAFETY VIOLATION: Empty database URL provided for test validation.")

    unquoted_raw = unquote(url).lower().replace('\\', '/')
    if "pgcb_portal.db" in unquoted_raw or "pgcb.db" in unquoted_raw:
        raise RuntimeError(
            f"SAFETY VIOLATION: Test suite cannot run against primary database file: {mask_url_credentials(url)}. "
            "Tests must never modify or connect to 'pgcb_portal.db'."
        )

    effective_env = (app_env if app_env is not None else os.environ.get("APP_ENV", "")).strip().lower()
    if effective_env in ("production", "staging"):
        raise RuntimeError(f"SAFETY VIOLATION: Cannot run test suite when APP_ENV={effective_env}!")

    try:
        parsed_url = make_url(url)
    except Exception as exc:
        raise RuntimeError(f"SAFETY VIOLATION: Invalid database URL format: {mask_url_credentials(url)}") from exc

    # Unconditional check: SQLite primary database references
    if parsed_url.drivername.startswith("sqlite"):
        db_file = parsed_url.database
        if db_file and db_file != ":memory:":
            db_unquoted = unquote(db_file).lower().replace('\\', '/')
            if "pgcb_portal" in db_unquoted or "pgcb.db" in db_unquoted:
                raise RuntimeError(
                    f"SAFETY VIOLATION: SQLite database target references primary database: {mask_url_credentials(url)}"
                )
            try:
                resolved_target = Path(unquote(db_file)).resolve()
                primary_portal = (Path(__file__).resolve().parents[2] / "pgcb_portal.db").resolve()
                if resolved_target == primary_portal:
                    raise RuntimeError(
                        f"SAFETY VIOLATION: SQLite database path resolves to primary database: {mask_url_credentials(url)}"
                    )
                if resolved_target.name.lower() in ("pgcb_portal.db", "pgcb.db"):
                    raise RuntimeError(
                        f"SAFETY VIOLATION: SQLite database filename matches primary database: {mask_url_credentials(url)}"
                    )
                if resolved_target.exists() and primary_portal.exists():
                    try:
                        if os.path.samefile(resolved_target, primary_portal):
                            raise RuntimeError(
                                f"SAFETY VIOLATION: SQLite database path is an alias/link to primary database: {mask_url_credentials(url)}"
                            )
                    except (OSError, ValueError):
                        pass
            except Exception as exc:
                if "SAFETY VIOLATION" in str(exc):
                    raise
        return

    # For non-SQLite (e.g. PostgreSQL, MySQL)
    host = (parsed_url.host or "").lower().strip("[]")
    database = unquote(parsed_url.database or "").lower()
    effective_port = parsed_url.port or 5432

    # 1. Unconditional check: Forbidden hostnames
    for f_host in FORBIDDEN_HOSTS:
        if f_host in host:
            raise RuntimeError(
                f"SAFETY VIOLATION: Test DATABASE_URL targets production infrastructure ({host}): {mask_url_credentials(url)}"
            )

    # 2. Unconditional check: Forbidden database names/keywords
    if any(keyword in database for keyword in FORBIDDEN_DB_KEYWORDS):
        raise RuntimeError(
            f"SAFETY VIOLATION: Database name '{database}' contains forbidden keyword "
            f"({FORBIDDEN_DB_KEYWORDS}). Tests must never target production or staging databases."
        )
    if database in PRIMARY_DB_NAMES:
        raise RuntimeError(
            f"SAFETY VIOLATION: Database name '{database}' is the primary application database name. "
            "Tests must never target the primary database directly."
        )

    # 3. Check parsed target authorization if AUTHORIZED_TEST_DB_TARGET is set
    target_str = os.environ.get("AUTHORIZED_TEST_DB_TARGET", "").strip()
    allow_external_flag = os.environ.get("ALLOW_EXTERNAL_TEST_DB", "").lower() in ("1", "true", "yes")
    allow_disposable_flag = os.environ.get("ALLOW_DISPOSABLE_TEST_DB", "").lower() in ("1", "true", "yes")

    # Conflicting broad boolean flags check
    if allow_external_flag and allow_disposable_flag:
        raise RuntimeError(
            "SAFETY VIOLATION: Conflicting authorization flags. Combining broad boolean "
            "ALLOW_EXTERNAL_TEST_DB and ALLOW_DISPOSABLE_TEST_DB is prohibited to prevent accidental "
            "targeting of arbitrary databases. Specify explicit AUTHORIZED_TEST_DB_TARGET='host[:port]/database'."
        )

    if target_str:
        try:
            t_host, t_port, t_database = parse_authorized_target(target_str)
        except ValueError as exc:
            raise RuntimeError(f"SAFETY VIOLATION: {exc}") from exc

        # Compare host
        if host != t_host:
            raise RuntimeError(
                f"SAFETY VIOLATION: Target host mismatch: target host is '{host}' "
                f"but AUTHORIZED_TEST_DB_TARGET specifies '{t_host}'."
            )

        # Compare port (if port was specified in target)
        if t_port is not None and effective_port != t_port:
            raise RuntimeError(
                f"SAFETY VIOLATION: Target port mismatch: effective port is '{effective_port}' "
                f"but AUTHORIZED_TEST_DB_TARGET specifies port '{t_port}'."
            )

        # Compare database
        if database != t_database:
            raise RuntimeError(
                f"SAFETY VIOLATION: Target database mismatch: target database is '{database}' "
                f"but AUTHORIZED_TEST_DB_TARGET specifies database '{t_database}'."
            )

        # Explicit parsed target matched and verified!
        return

    # Standard approved CI/local target: approved host + approved test DB name/suffix
    is_standard_host = host in APPROVED_TEST_HOSTS
    is_standard_db = (database in APPROVED_TEST_DB_NAMES) or any(database.endswith(sfx) for sfx in APPROVED_TEST_DB_SUFFIXES)

    if is_standard_host and is_standard_db:
        return

    # Non-standard target without explicit AUTHORIZED_TEST_DB_TARGET:
    if not is_standard_host:
        if allow_external_flag and is_standard_db:
            return
        elif allow_external_flag and not is_standard_db:
            raise RuntimeError(
                f"SAFETY VIOLATION: External host '{host}' with non-standard database '{database}' "
                f"requires explicit AUTHORIZED_TEST_DB_TARGET='{host}:{effective_port}/{database}' matching host, port, and database."
            )
        else:
            raise RuntimeError(
                f"SAFETY VIOLATION: PostgreSQL test target host '{host}' is not in approved test host list "
                f"({sorted(APPROVED_TEST_HOSTS)}). Specify AUTHORIZED_TEST_DB_TARGET='{host}:{effective_port}/{database}' to authorize."
            )

    if not is_standard_db:
        if allow_disposable_flag and is_standard_host:
            return
        else:
            raise RuntimeError(
                f"SAFETY VIOLATION: Destructive test target database name '{database}' is not an authorized test database. "
                f"Must be one of {sorted(APPROVED_TEST_DB_NAMES)}, end with {APPROVED_TEST_DB_SUFFIXES}, "
                f"or specify AUTHORIZED_TEST_DB_TARGET='{host}:{effective_port}/{database}'."
            )


def assert_destructive_database_permitted(
    url: str,
    action_name: str = "destructive database operation",
    app_env: str | None = None,
) -> None:
    """
    Fail-closed guard for destructive database operations (schema drop/create,
    synthetic member generation, test table reset, test fixture seeding).

    Enforces:
    1. APP_ENV must be explicitly defined and recognized as a safe environment
       (e.g. 'test', 'development', 'dev', 'local'). Missing, empty, misspelled
       (e.g. 'prodution', 'tst'), or unexpected APP_ENV values are denied fail-closed.
    2. Operations in 'production' or 'staging' are unconditionally denied.
    3. If APP_ENV is 'test' or if the action is test-related, the target URL must
       strictly satisfy validate_test_database_url(url).
    4. Even in non-test safe environments (e.g. 'development'), forbidden hosts
       and forbidden keywords ('prod', 'staging', 'live') are blocked.
    """
    effective_env = (app_env if app_env is not None else os.environ.get("APP_ENV", "")).strip().lower()

    # Fail closed on empty or unset APP_ENV
    if not effective_env:
        raise RuntimeError(
            f"SAFETY VIOLATION: Destructive operation '{action_name}' denied. "
            "APP_ENV is unset or empty. Must be explicitly set to a recognized safe environment: "
            f"{sorted(SAFE_DESTRUCTIVE_ENVIRONMENTS)}."
        )

    # Fail closed on unrecognized / misspelled APP_ENV
    if effective_env not in SAFE_DESTRUCTIVE_ENVIRONMENTS:
        raise RuntimeError(
            f"SAFETY VIOLATION: Destructive operation '{action_name}' denied in APP_ENV='{effective_env}'. "
            f"Destructive operations are strictly restricted to: {sorted(SAFE_DESTRUCTIVE_ENVIRONMENTS)}."
        )

    if not url or not str(url).strip():
        raise RuntimeError(f"SAFETY VIOLATION: Destructive operation '{action_name}' denied. Empty database URL.")

    # Check primary SQLite database file
    unquoted_raw = unquote(url).lower().replace('\\', '/')
    is_test_op = (effective_env == "test") or ("test" in action_name.lower())

    if is_test_op:
        if "pgcb_portal.db" in unquoted_raw or "pgcb.db" in unquoted_raw:
            raise RuntimeError(
                f"SAFETY VIOLATION: Destructive test operation '{action_name}' cannot target "
                f"primary database file: {mask_url_credentials(url)}."
            )
        # In test mode, enforce full test database authorization
        validate_test_database_url(url, app_env=effective_env)
        return

    # In dev/local: ensure URL does not target production hostnames or database names
    try:
        parsed_url = make_url(url)
    except Exception as exc:
        raise RuntimeError(f"SAFETY VIOLATION: Invalid database URL format for '{action_name}': {mask_url_credentials(url)}") from exc

    if not parsed_url.drivername.startswith("sqlite"):
        host = (parsed_url.host or "").lower().strip("[]")
        database = unquote(parsed_url.database or "").lower()

        for f_host in FORBIDDEN_HOSTS:
            if f_host in host:
                raise RuntimeError(
                    f"SAFETY VIOLATION: Destructive operation '{action_name}' targets "
                    f"forbidden production infrastructure host '{host}': {mask_url_credentials(url)}"
                )

        if any(keyword in database for keyword in FORBIDDEN_DB_KEYWORDS):
            raise RuntimeError(
                f"SAFETY VIOLATION: Destructive operation '{action_name}' targets "
                f"forbidden database '{database}' containing production keywords: {mask_url_credentials(url)}"
            )


def is_test_migration_active(app_env: str | None = None) -> bool:
    """
    Check if a migration is running in test mode.
    Returns True if:
      - running inside an active pytest execution (PYTEST_CURRENT_TEST is set), OR
      - APP_ENV is 'test', OR
      - ALEMBIC_TEST_MODE is enabled (provided APP_ENV is not explicitly production/staging).
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True

    effective_env = (app_env if app_env is not None else os.environ.get("APP_ENV", "")).strip().lower()
    if effective_env in ("production", "staging"):
        return False

    return (
        effective_env == "test"
        or os.environ.get("ALEMBIC_TEST_MODE", "").lower() in ("1", "true", "yes")
    )
