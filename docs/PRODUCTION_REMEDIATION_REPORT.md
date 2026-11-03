# PGCB Organization Portal — Production Remediation Report
**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Target Platform:** HostSeba cPanel / CloudLinux / Phusion Passenger / LiteSpeed  
**Release:** `v1.0.0-rc1`  
**Frontend:** `https://powergriddiprocoush.org`  
**API Subdomain:** `https://api.powergriddiprocoush.org`  
**Runtime:** Python 3.11.17 + PostgreSQL (Psycopg 3)

---

## 1. Executive Summary

This report documents the end-to-end production audit, security hardening, and deployment remediation executed for the PGCB Organization Portal backend. The remediation eliminates the root causes that previously prevented the FastAPI backend from running under HostSeba's CloudLinux Phusion Passenger / LiteSpeed shared hosting environment, hardens authentication, session management, and CSRF protection, and establishes a robust, manual cPanel deployment pathway that requires **zero SSH or terminal access**.

All existing business logic, database models, schemas, and member records (including the 3.8 MB local database `pgcb_portal.db`) were preserved without modification.

---

## 2. Root Cause Analysis & Resolutions

### 2.1 ASGI-to-WSGI Passenger Adaptation & LiteSpeed Application Discovery
- **Problem:** LiteSpeed Web Server and Phusion Passenger on HostSeba expect a synchronous WSGI entry point (`application`). Furthermore, LiteSpeed's LSAPI module looks specifically for `wsgi.py` in the application root, logging `cannot determine application type` and returning 404 when only `passenger_wsgi.py` is present.
- **Resolution:**
  1. Maintained `services/api/passenger_wsgi.py` using `a2wsgi.ASGIMiddleware` to bridge FastAPI's asynchronous ASGI application to Passenger's WSGI interface.
  2. Implemented `services/api/wsgi.py` as a canonical entry point that cleanly imports and exposes `application = passenger_wsgi.application`.
  3. Added multi-path virtual environment auto-detection supporting both CloudLinux cPanel paths (`/home/powergri/virtualenv/...`) and local development directories.

### 2.2 Truthful Health Check Architecture
- **Problem:** The previous `/health` endpoint returned a hardcoded JSON response `{"status": "ok", "database": "connected"}` without querying the database, masking connection failures and misleading external monitoring.
- **Resolution:**
  1. Updated `/health` (and `/api/v1/health`, `/healthz`) to execute a dynamic `SELECT 1` query via SQLAlchemy. If the database is responsive, it returns `{"status": "ok", "database": "connected"}`. If unreachable, it returns `{"status": "degraded", "database": "unavailable"}` and logs a diagnostic warning without crashing.
  2. Maintained `/ready` (and `/readyz`) to test `SELECT 1`, returning HTTP 200 `{"status": "ready", "database": "ok"}` on success, and HTTP 503 `{"status": "not_ready", "database": "error", "detail": "Database unavailable"}` when down.
  3. Maintained `/live` as a pure process liveness probe returning `{"status": "alive", "service": "pgcb-api"}` without any database dependency, preventing cascade restart loops during transient database maintenance.

### 2.3 PostgreSQL Production Configuration & Driver Normalization
- **Problem:** Configuration settings previously lacked dialect enforcement for Psycopg 3 (`postgresql+psycopg://`), and production environments were at risk of falling back to ephemeral local SQLite databases.
- **Resolution:**
  1. Configured automatic dialect normalization in `app.core.config.Settings`: all `postgres://`, `postgresql://`, and `postgresql+psycopg2://` URLs are automatically rewritten to `postgresql+psycopg://`.
  2. Added discrete credential builders (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`) with URL-encoding (`quote_plus`) for special characters.
  3. Enforced `allow_sqlite_in_production = False` by default in staging/production. If `DATABASE_URL` specifies SQLite in production without `ALLOW_SQLITE_IN_PRODUCTION=true`, the application fails fast at startup with an explanatory message.

### 2.4 Fail-Fast Startup Error Handling & Credential Masking
- **Problem:** When backend startup failed, Passenger previously served a generic 404 or caught the exception and served a mock 500 fallback that concealed configuration errors. Additionally, raw database connection strings containing passwords could leak into server logs.
- **Resolution:**
  1. Updated `passenger_wsgi.py` so that in production (`APP_ENV=production`), startup exceptions are logged to stderr and `services/api/passenger_startup.log` and then re-raised immediately (`raise startup_exc`), ensuring cPanel logs the exact failure condition.
  2. Implemented `mask_sensitive_data()` in `passenger_wsgi.py` and `run_migrations.py` to scrub database passwords (`://user:***@host`), JWT secrets, and API tokens before writing to any log file.

### 2.5 Origin-Based CSRF Protection & CORS Hardening
- **Problem:** When authentication tokens are stored in browser session cookies (`pgcb_access_token`), cross-site requests to state-changing endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) could be vulnerable to CSRF if origin headers were not verified.
- **Resolution:**
  1. Updated `SecurityMiddleware` to inspect state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) that carry the session cookie without an `Authorization: Bearer` header.
  2. Verified `Origin` and `Referer` against the allowed CORS origins set (`FRONTEND_URL`, `ALLOWED_ORIGINS`). Cross-site browser requests with untrusted origins are rejected with HTTP 403 Forbidden (`{"detail": "CSRF origin verification failed"}`).
  3. Added `X-CSRF-Token` and `Accept` to `CORSMiddleware.allow_headers` in `app.main`.

### 2.6 Zero-Downtime MFA Key Rotation
- **Problem:** MFA secret keys stored in the database are encrypted using Fernet. If the key was rotated or `MFA_ENCRYPTION_KEY` was newly introduced, previously enrolled users could not decrypt their TOTP secrets.
- **Resolution:**
  1. Updated `app.core.mfa.decrypt_secret()` to attempt primary decryption using `settings.mfa_encryption_key`.
  2. If primary decryption fails, it falls back to the legacy derived Fernet key (`hashlib.sha256(jwt_secret)`), enabling zero-downtime key rotation while preserving existing user MFA credentials.
  3. Added strict validation in `app.core.config.Settings` ensuring any configured `MFA_ENCRYPTION_KEY` is a valid 32-byte urlsafe base64 Fernet key.

### 2.7 Persistent Storage Subdirectory Initialization
- **Problem:** Missing storage subdirectories could cause unhandled `FileNotFoundError` during document uploads.
- **Resolution:**
  1. Updated `DiskStorageBackend.ensure_root_exists()` in `app.storage.disk` to automatically create all required subdirectories on startup: `public`, `members`, `cards`, `certificates`, `documents`, and `member_documents`.

### 2.8 Manual cPanel Deployment Utilities (Zero-Terminal Access)
- **Problem:** HostSeba shared hosting accounts frequently do not include SSH shell access, preventing manual execution of `alembic upgrade head` or admin creation CLI commands.
- **Resolution:**
  1. Created `services/api/scripts/run_migrations.py`: A self-contained migration script that can be executed directly from cPanel's **Setup Python App** $\to$ **Execute python script** field. It executes Alembic migrations programmatically and writes a persistent audit log to `services/api/migration_run.log`.
  2. Hardened `services/api/app/scripts/create_admin.py` with standalone `sys.path` bootstrap, allowing administrators to bootstrap or update the `SUPER_ADMIN` account directly through cPanel.

---

## 3. Verification & Test Evidence

All automated test suites were executed against the updated codebase:
- **Health Checks & Readiness (`test_health_checks.py`):** 5/5 PASSED
  - `/live`: Returns HTTP 200 without database access.
  - `/health`: Returns HTTP 200 with `status: ok` and `database: connected` when DB is healthy.
  - `/health`: Returns HTTP 200 with `status: degraded` and `database: unavailable` when DB is disconnected.
  - `/ready`: Returns HTTP 200 when DB is healthy; returns HTTP 503 `detail: Database unavailable` when DB is down.
- **CSRF & Security Middleware (`test_csrf_and_security.py`):** 5/5 PASSED
  - Rejects cookie-authenticated POST with untrusted Origin (HTTP 403).
  - Rejects cookie-authenticated POST with untrusted Referer (HTTP 403).
  - Allows cookie-authenticated POST with trusted frontend Origin.
  - Allows Bearer-authenticated POST from any client without CSRF restrictions.
  - Allows safe GET requests.
- **MFA Encryption & Rotation (`test_mfa_rotation.py`):** 3/3 PASSED
  - Validates encryption and decryption with legacy derived key.
  - Validates zero-downtime key rotation with fallback decryption.
  - Validates rejection of invalid non-base64 `MFA_ENCRYPTION_KEY`.

---

## 4. Status and Next Steps

The backend repository is fully remediated, hardened, and verified for HostSeba cPanel production deployment. Proceed to `docs/HOSTSEBA_DEPLOYMENT_GUIDE.md` for the exact cPanel deployment instructions.
