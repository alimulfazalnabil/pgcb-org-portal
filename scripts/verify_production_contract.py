#!/usr/bin/env python3
"""
PGCB Organization Portal - Production Contract Pre-Flight Validator
Validates the environment, configuration, and dependencies before deployment.
Never prints secret values in output.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add services/api and repo root to sys.path so project modules can be loaded
_repo_root = Path(__file__).resolve().parent.parent
_api_dir = _repo_root / "services" / "api"
for path in (_repo_root, _api_dir):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def mask(value: str | None, min_len: int = 4) -> str:
    """Safely mask secret values showing only length and presence."""
    if not value:
        return "[NOT SET]"
    return f"[SET (len={len(value)})]"


def check_contract(mode: str) -> bool:
    print("=" * 70)
    print(f" PGCB PORTAL PRODUCTION CONTRACT PRE-FLIGHT CHECK | MODE: {mode.upper()}")
    print("=" * 70)

    # Load environment variables
    app_env = os.getenv("APP_ENV", mode).lower()
    db_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "")
    storage_backend = os.getenv("STORAGE_BACKEND", "azure" if app_env == "production" else "local").lower()
    azure_conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_acc = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
    azure_container = os.getenv("AZURE_STORAGE_CONTAINER", "pgcb-files")
    jwt_secret = os.getenv("JWT_SECRET", "")
    mfa_key = os.getenv("MFA_ENCRYPTION_KEY", "")
    frontend_url = os.getenv("FRONTEND_URL", "")

    failures = []
    warnings = []

    # 1. Environment & Mode
    print(f"[*] Target Environment : {app_env}")

    # 2. Database URL Validation
    if not db_url:
        if app_env == "production":
            failures.append("DATABASE_URL is missing. Production requires a managed PostgreSQL connection string.")
        else:
            warnings.append("DATABASE_URL is empty; will default to sqlite:///./pgcb_portal.db in dev/test.")
        print(f"[-] DATABASE_URL       : [MISSING]")
    else:
        # Check dialect
        normalized_url = db_url
        if db_url.startswith("postgres://"):
            normalized_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://"):
            normalized_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql+psycopg2://"):
            normalized_url = db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

        driver = normalized_url.split(":")[0]
        if app_env == "production" and not driver.startswith("postgresql+psycopg"):
            failures.append(f"DATABASE_URL driver is '{driver}'. Production requires 'postgresql+psycopg://'.")
            print(f"[!] DATABASE_URL       : {driver}://... [INVALID DRIVER FOR PSYCOPG 3]")
        else:
            print(f"[+] DATABASE_URL       : {driver}://... {mask(db_url)}")

    # 3. Redis URL Validation
    if not redis_url:
        if app_env == "production":
            warnings.append("REDIS_URL is missing; Celery and distributed rate-limiting will be degraded.")
            print(f"[!] REDIS_URL          : [NOT SET]")
        else:
            print(f"[*] REDIS_URL          : [DEFAULTING TO LOCAL]")
    else:
        scheme = redis_url.split("://")[0] if "://" in redis_url else "unknown"
        if scheme in ("redis", "rediss"):
            print(f"[+] REDIS_URL          : {scheme}://... {mask(redis_url)}")
        else:
            warnings.append(f"Unrecognized Redis scheme '{scheme}'")
            print(f"[!] REDIS_URL          : {scheme}://... {mask(redis_url)}")

    # 4. Storage Backend Validation
    print(f"[*] STORAGE_BACKEND    : {storage_backend}")
    if app_env == "production":
        if storage_backend != "azure":
            failures.append(
                f"STORAGE_BACKEND is '{storage_backend}'. Production strictly requires 'azure' "
                f"to prevent permanent data loss when container instances restart."
            )
            print(f"[-] STORAGE_BACKEND    : '{storage_backend}' [MUST BE 'azure' IN PRODUCTION]")
        else:
            if not (azure_conn or azure_acc):
                failures.append(
                    "Azure Blob Storage credentials missing. Set AZURE_STORAGE_CONNECTION_STRING "
                    "or AZURE_STORAGE_ACCOUNT_URL in environment or shared-secrets."
                )
                print("[-] AZURE_STORAGE_CONN : [MISSING REQUIRED CREDENTIALS]")
            else:
                cred_type = "connection_string" if azure_conn else "account_url"
                val = azure_conn or azure_acc
                print(f"[+] AZURE_STORAGE_CONN : ({cred_type}) {mask(val)}")
            print(f"[+] AZURE_CONTAINER    : '{azure_container}'")
    else:
        print(f"[+] STORAGE_BACKEND    : '{storage_backend}' (permitted in {app_env})")

    # 5. Security Credentials Validation
    if not jwt_secret:
        if app_env == "production":
            failures.append("JWT_SECRET is missing. Production requires a secret with at least 32 characters.")
            print("[-] JWT_SECRET         : [MISSING]")
        else:
            warnings.append("JWT_SECRET is empty; will use insecure default in dev/test.")
            print("[-] JWT_SECRET         : [USING DEV DEFAULT]")
    elif len(jwt_secret) < 32 and app_env == "production":
        failures.append(f"JWT_SECRET is too short ({len(jwt_secret)} chars). Minimum length is 32.")
        print(f"[-] JWT_SECRET         : {mask(jwt_secret)} [TOO SHORT (<32)]")
    elif jwt_secret.startswith("dev-only-secret") and app_env == "production":
        failures.append("JWT_SECRET is set to the default placeholder. Provide a secure random secret.")
        print("[-] JWT_SECRET         : [INSECURE DEFAULT VALUE]")
    else:
        print(f"[+] JWT_SECRET         : {mask(jwt_secret)}")

    if not mfa_key and app_env == "production":
        warnings.append("MFA_ENCRYPTION_KEY is not set. MFA totp secrets will not be encrypted at rest.")
        print("[-] MFA_ENCRYPTION_KEY : [NOT SET (WARNING)]")
    else:
        print(f"[+] MFA_ENCRYPTION_KEY : {mask(mfa_key)}")

    # 6. Frontend URL (CORS / Redirects)
    if not frontend_url and app_env == "production":
        warnings.append("FRONTEND_URL is not set. CORS will default to localhost.")
        print("[-] FRONTEND_URL       : [NOT SET]")
    else:
        print(f"[+] FRONTEND_URL       : {frontend_url or 'http://localhost:3000'}")

    # Summary
    print("-" * 70)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  * {w}")

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  ! {f}")
        print("=" * 70)
        print("RESULT: PRE-FLIGHT CHECK FAILED - Resolve the failures above before deploying.")
        print("=" * 70)
        return False

    print("=" * 70)
    print("RESULT: PRE-FLIGHT CHECK PASSED - Environment satisfies production contract.")
    print("=" * 70)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PGCB Portal deployment contract")
    parser.add_argument(
        "--mode",
        choices=["production", "development", "test"],
        default=os.getenv("APP_ENV", "production").lower(),
        help="Target environment mode to validate (default: from APP_ENV or production)",
    )
    args = parser.parse_args()
    success = check_contract(args.mode)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
