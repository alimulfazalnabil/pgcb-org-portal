# Step 7D — Production Passenger Startup Failure Verification

**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Target Environment:** HostSeba Shared Hosting / CloudLinux / LiteSpeed Web Server / Phusion Passenger  
**Production API:** `https://api.powergriddiprocoush.org`  
**Python Runtime:** 3.11.18  
**Repository Working Directory:** `C:/Users/aflna/Downloads/pgcb-org-portal-v1.0`  
**Audit Date:** November 4, 2026  
**Investigation Mode:** READ-ONLY Verification  

---

## 1. Status of Repository `passenger_startup.log`

### Audit Finding: **HISTORICAL LOCAL TEST LOG (NOT LIVE SERVER LOG)**

Inspection of `services/api/passenger_startup.log` in the local repository revealed:
- **Total Lines:** 514 lines.
- **Paths in Tracebacks:** All stack traces reference local Windows filesystem paths:
  ```text
  File "C:\Users\aflna\Downloads\pgcb-org-portal-v1.0\services\api\passenger_wsgi.py", line 156, in <module>
  File "C:\Users\aflna\Downloads\pgcb-org-portal-v1.0\services\api\tests\unit\test_passenger_wsgi.py", line 211, in mock_import
  ```
- **Error Types:** `ImportError: No module named 'a2wsgi'` followed by `RuntimeError: Critical Deployment Error: 'a2wsgi' is required to run FastAPI under Phusion Passenger WSGI...`
- **Origin:** These entries were generated locally on the developer workstation during unit test runs of `services/api/tests/unit/test_passenger_wsgi.py`, where `a2wsgi` import failure was intentionally mocked to test error handling and log formatting.
- **Server Evidence Status:** The repository log contains **zero** entries from the live HostSeba server (`/home/powergri/...`). The actual live server startup log resides strictly on the HostSeba filesystem at `/home/powergri/repositories/pgcb-org-portal/services/api/passenger_startup.log`.

---

## 2. Inspection of `passenger_wsgi.py` Startup Exception Handler

In `services/api/passenger_wsgi.py` (lines 145–180), process initialization is governed by this logic:

```python
# 4. Attempt application initialization with strict fail-fast behavior in production
application = None
_startup_error_detail: str | None = None

try:
    from app.main import app as asgi_app

    try:
        from a2wsgi import ASGIMiddleware
    except ImportError as exc:
        raise RuntimeError(
            "Critical Deployment Error: 'a2wsgi' is required to run FastAPI under "
            "Phusion Passenger WSGI. Ensure 'a2wsgi' is installed in your Python environment "
            "(pip install -r requirements.txt)."
        ) from exc

    application = ASGIMiddleware(asgi_app)

except Exception as startup_exc:
    _startup_error_detail = _log_startup_error(startup_exc)
    allow_dev_fallback = os.environ.get("ALLOW_STARTUP_FALLBACK", "").lower() in ("true", "1", "yes")
    if _IS_PRODUCTION and not allow_dev_fallback:
        # In staging/production, fail immediately and loudly so startup failures are unmistakable
        raise startup_exc
    application = create_fallback_application(startup_exc)
```

### Critical Architectural Invariants:
1. **Diagnostic Logging Mechanism:** When an exception occurs, `_log_startup_error(startup_exc)` formats the full traceback, runs regex credential masking, writes the error to `sys.stderr` (captured by LiteSpeed), and **appends the masked traceback to `API_DIR / "passenger_startup.log"`**.
2. **Production Fail-Fast Policy:** Because `_IS_PRODUCTION` is `True` by default (`APP_ENV=production`), `raise startup_exc` is executed.
3. **HTTP 500 Generation:** In WSGI specifications, when an unhandled exception escapes a startup script during worker initialization, Phusion Passenger aborts the worker and emits an unhandled **HTTP 500 Internal Server Error**.

---

## 3. Configuration Validation Trace Before Application Creation

Tracing the exact sequence of operations triggered by `from app.main import app as asgi_app`:

```text
passenger_wsgi.py: line 149
  └── from app.main import app as asgi_app
        └── app/main.py: line 9
              └── from app.core.config import settings
                    └── app/core/config.py: line 191
                          └── settings = Settings()
```

When `Settings()` is instantiated:
1. **Pydantic BaseSettings Initializer:**
   - Reads existing environment variables from `os.environ`.
   - Reads `.env` and `.env.production` from `services/api/` and the repository root (if present).
2. **`@model_validator(mode='after') def validate_production(self)` Execution:**
   - Normalizes and strips whitespace/quotes from `jwt_secret` and `secret_key`.
   - If `mfa_encryption_key` is provided: attempts `Fernet(self.mfa_encryption_key.encode())`. If not a 32-byte urlsafe base64 key, raises `ValueError`.
   - Resolves `storage_root` (falls back to `./storage` if empty).
   - If `db_host`, `db_user`, `db_password` are set: constructs `postgresql+psycopg://...`.
   - Normalizes legacy URL schemes (`postgres://`, `postgresql://`, `postgresql+psycopg2://`) to `postgresql+psycopg://`.
   - **Production Hardening Block (`if self.app_env.lower() in ('production', 'staging'):`):**
     - **Check A (JWT Secret):** If `jwt_secret` is empty or starts with `'dev-only-secret'`, raises:  
       `ValueError('JWT_SECRET is missing or using the development placeholder...')`
     - **Check B (JWT Length):** If `len(jwt_secret) < 32`, raises:  
       `ValueError('JWT_SECRET is too short...')`
     - **Check C (Storage Driver):** If `storage_backend` is not `'local'`, `'filesystem'`, or `'persistent_disk'`, raises:  
       `ValueError(...)`
     - **Check D (Database Scheme):** If `database_url` starts with `'sqlite'`, raises:  
       `ValueError("Staging/Production configuration invalid: DATABASE_URL cannot be SQLite. A valid PostgreSQL connection string ('postgresql+psycopg://...') is strictly required.")`
     - **Check E (Database Driver):** If `database_url` does not start with `'postgresql+psycopg://'`, raises:  
       `ValueError("Invalid database driver in DATABASE_URL for staging/production... Must use 'postgresql+psycopg://'")`

### Crucial Finding on Lazy Resource Binding:
- **No Database Connection at Import:** Line 11 of `app/main.py` creates SQLAlchemy's `engine = create_engine(...)`. SQLAlchemy engines connect lazily upon the first query checkout. Database connectivity is **not** verified during module import.
- **No Storage Disk I/O at Import:** Storage root creation (`ensure_root_exists()`) and database verification are encapsulated inside the `lifespan(app: FastAPI)` context manager, which runs only after Passenger begins processing requests.
- **Conclusion:** A module import failure during startup can be caused **strictly by**:
  1. A Python `ImportError` / `ModuleNotFoundError` (e.g. missing `a2wsgi`, `fastapi`, `psycopg`, etc.).
  2. A Pydantic `ValueError` from `validate_production()` due to missing production environment variables.

---

## 4. Production Environment Variables Inventory

| Variable Name | Required for Startup? | Default Value | Production Validation Constraint | Primary Source | Fallback Source | Failure Consequence |
|---|:---:|---|---|---|---|---|
| `APP_ENV` | **Yes** | `development` | Must be `production` or `staging` | Set by `passenger_wsgi.py` (`setdefault`) | cPanel Python App GUI | Runs in dev mode if unset; in production triggers strict checks |
| `DATABASE_URL` | **Yes** | `sqlite:///./pgcb_portal.db` | Must start with `postgresql+psycopg://` (SQLite strictly blocked) | cPanel Environment variables | `services/api/.env` | **Immediate startup `ValueError` -> HTTP 500** |
| `JWT_SECRET` | **Yes** | `dev-only-secret-...` | Minimum 32 random characters; cannot use dev placeholder | cPanel Environment variables | `services/api/.env` | **Immediate startup `ValueError` -> HTTP 500** |
| `STORAGE_ROOT` | No | `./storage` | Defaults to `/home/powergri/storage` | cPanel Environment variables | `services/api/.env` | Defaults to `./storage`; non-fatal at startup |
| `FRONTEND_URL` | No | `http://localhost:3000` | Normalized URL string | cPanel Environment variables | `services/api/.env` | Non-fatal at startup |
| `ALLOWED_ORIGINS` | No | `None` | Comma-separated origins | cPanel Environment variables | `services/api/.env` | Non-fatal at startup |
| `MFA_ENCRYPTION_KEY` | No | `None` | If provided, must be valid 32-byte Fernet base64 | cPanel Environment variables | `services/api/.env` | **Fatal `ValueError` if malformed**; non-fatal if absent |
| `ALLOW_STARTUP_FALLBACK` | No | `false` | Boolean (`true`/`false`) | cPanel Environment variables | `services/api/.env` | If `true`, returns 500 JSON instead of crash |

---

## 5. Review of Deployment Configuration Templates

### 5.1 `deployment/hostseba/api_subdomain_htaccess.example`
- **Purpose:** Configuration for the API Document Root (`/home/powergri/api.powergriddiprocoush.org/.htaccess`).
- **Directives:**
  ```apache
  # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
  PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"
  PassengerBaseURI "/"
  PassengerPython "/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/python"
  # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

  PassengerEnabled on
  PassengerAppType wsgi
  PassengerStartupFile passenger_wsgi.py
  ```
- **Evaluation:** Fully verified. Binds Passenger to root `/`, tells LiteSpeed where the Python virtualenv and application root live, and delegates request routing to `passenger_wsgi.py`.

### 5.2 `deployment/hostseba/htaccess.example`
- **Purpose:** Configuration for the main frontend web root (`/home/powergri/public_html/.htaccess`).
- **Directives:**
  ```apache
  RewriteRule ^backend/(.*)$ https://api.powergriddiprocoush.org/$1 [P,L]
  ProxyPassReverse /backend/ https://api.powergriddiprocoush.org/

  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^(.*)$ http://127.0.0.1:3000/$1 [P,L]
  ProxyPassReverse / http://127.0.0.1:3000/
  ```
- **Evaluation:** Forwards all browser requests targeting `/backend/*` to the independent API subdomain.

### 5.3 `deployment/hostseba/PATCH_README.md`
- Documents the historical DocumentRoot probe diagnostic (`probe.txt`), confirming that cPanel frequently creates nested paths like `/home/powergri/home/powergri/...` when full paths are typed into the cPanel Subdomain form.

---

## 6. Compatibility Analysis: Dedicated Document Root vs. cPanel Python App

### Architectural Question:
*Is a dedicated DocumentRoot (`/home/powergri/api.powergriddiprocoush.org`) compatible with an Application Root located at `/home/powergri/repositories/pgcb-org-portal/services/api`?*

### Technical Proof: **YES — 100% COMPATIBLE AND STRONGLY RECOMMENDED**

1. **Phusion Passenger Decoupled Architecture:**  
   Phusion Passenger was explicitly engineered to separate static document serving from backend code execution:
   - **DocumentRoot:** The public entry directory where LiteSpeed receives incoming web requests and evaluates `.htaccess`.
   - **PassengerAppRoot:** The directory where backend application logic, virtual environments, and entry points reside.
2. **Isolation from Frontend Rewrites:**  
   If the API DocumentRoot is placed inside `/home/powergri/public_html/api`, it is a subdirectory of `public_html`. Apache and LiteSpeed process `.htaccess` hierarchically. Any rewrite rule in `/home/powergri/public_html/.htaccess` (such as proxying unmatched requests to port 3000) will intercept or corrupt API requests heading into `public_html/api`. Placing the DocumentRoot at `/home/powergri/api.powergriddiprocoush.org` provides total isolation.
3. **CloudLinux Standard Topology:**  
   When CloudLinux's "Setup Python App" is configured with:
   - Application URL: `api.powergriddiprocoush.org`
   - Application root: `repositories/pgcb-org-portal/services/api`
   CloudLinux automatically sets `PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"` in the DocumentRoot `.htaccess`.

---

## 7. Clarification of Hosting Terminology

To prevent operational confusion during cPanel administration:

| Term | What It Represents | Actual HostSeba Path / Setting | Where It Is Configured |
|---|---|---|---|
| **Document Root** | The filesystem directory that LiteSpeed exposes to the web for a domain. Where LiteSpeed checks for `.htaccess` and static files. | `/home/powergri/api.powergriddiprocoush.org` | cPanel **Domains** (or **Subdomains**) |
| **Application Root** | The directory containing backend application source code, dependencies, and configuration. | `/home/powergri/repositories/pgcb-org-portal/services/api` | cPanel **Setup Python App** $\to$ *Application root* |
| **Passenger Application URL** | The domain/subdomain bound to the Python application. | `api.powergriddiprocoush.org` | cPanel **Setup Python App** $\to$ *Application URL* |
| **Passenger Startup File** | The script executed by Passenger to bootstrap the WSGI callable. | `passenger_wsgi.py` | cPanel **Setup Python App** $\to$ *Application startup file* |

---

## 8. Safe cPanel Procedure to Retrieve Live Evidence

Follow this step-by-step procedure to inspect live server state without altering any files or executing migrations:

### Step 1 — Retrieve the Actual Live Startup Exception Traceback
1. Log into HostSeba cPanel (`https://hydra.hostseba.com:2083`).
2. Open **File Manager**.
3. In the top-right corner, click **Settings**, check **"Show Hidden Files (dotfiles)"**, and click **Save**.
4. Navigate to:  
   `/home/powergri/repositories/pgcb-org-portal/services/api/`
5. Locate the file **`passenger_startup.log`**:
   - Right-click $\to$ **View** (Read-Only).
   - Scroll to the bottom of the file to see the most recent traceback.
   - **Record:** The exact exception message (e.g., `ModuleNotFoundError: No module named 'a2wsgi'` OR `ValueError: Staging/Production configuration invalid: DATABASE_URL cannot be SQLite` OR `ValueError: JWT_SECRET is missing...`).
6. If `passenger_startup.log` is empty, check `/home/powergri/logs/` or `/home/powergri/stderr.log` for LiteSpeed error entries.

### Step 2 — Verify Active Document Root Mapping in cPanel
1. In cPanel, navigate to **Domains** (or **Subdomains**).
2. Locate the row for **`api.powergriddiprocoush.org`**.
3. Check the path shown under the **Document Root** column:
   - Does it say `/home/powergri/api.powergriddiprocoush.org`?
   - Or does it say `/home/powergri/public_html/api`?
   - Or does it say `/home/powergri/home/powergri/api.powergriddiprocoush.org`?
4. **Record:** The exact Document Root path currently configured in cPanel.

### Step 3 — Inspect `.htaccess` in the Active Document Root
1. In cPanel **File Manager**, navigate into the Document Root identified in Step 2.
2. Check if `.htaccess` exists:
   - Right-click $\to$ **View**.
   - Check if lines 1–6 contain:
     ```apache
     PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"
     PassengerEnabled on
     PassengerStartupFile passenger_wsgi.py
     ```
3. **Record:** Whether `.htaccess` exists and whether `PassengerEnabled on` is present.

### Step 4 — Check Environment Variables and Virtualenv in Setup Python App
1. In cPanel, navigate to **Software** $\to$ **Setup Python App**.
2. Click the edit icon for `api.powergriddiprocoush.org`.
3. Scroll to **Environment variables**:
   - Check if `DATABASE_URL` is listed with a `postgresql+psycopg://` URI.
   - Check if `JWT_SECRET` is listed with $\ge 32$ characters.
4. **Record:** Whether `DATABASE_URL` and `JWT_SECRET` are present in the cPanel GUI table.

---

## 9. Categorization of Investigation Findings

### CONFIRMED FINDINGS
1. **Repository Log is Local:** `services/api/passenger_startup.log` in the Git repository is a local Windows test log, not a live HostSeba log.
2. **Phase 1 Root Cause:** LiteSpeed attempted to open `/home/powergri/api.powergriddiprocoush.org/health` as a static file and logged `File not found` because the DocumentRoot lacked active Passenger directives.
3. **Fail-Fast Policy:** `passenger_wsgi.py` unconditionally re-raises startup exceptions in `production`, causing Phusion Passenger to return HTTP 500 when module loading fails.
4. **Endpoint Independence:** Neither `/health` nor `/live` in FastAPI can return HTTP 500 due to database failure; both handle database unavailability with 200 or 503.
5. **Path Compatibility:** An isolated DocumentRoot (`/home/powergri/api.powergriddiprocoush.org`) is 100% architecturally compatible with `PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"`.

### PROBABLE FINDINGS
1. **Missing Production Secrets in LiteSpeed Process:** The HTTP 500 after DocumentRoot restoration is probably caused by `Settings.validate_production()` failing on SQLite default or placeholder `JWT_SECRET`, due to cPanel GUI variables failing to propagate to Passenger child processes without a local `.env`.
2. **Missing `a2wsgi` in Virtualenv:** If pip install was not executed on `requirements.txt` in the CloudLinux virtualenv, `passenger_wsgi.py` crashes on `from a2wsgi import ASGIMiddleware`.

### UNVERIFIED FINDINGS (Requires Live Server Inspection)
1. The exact exception text inside `/home/powergri/repositories/pgcb-org-portal/services/api/passenger_startup.log` on HostSeba.
2. The current active DocumentRoot in cPanel Domains (`public_html/api` vs `api.powergriddiprocoush.org`).
3. The presence of `a2wsgi` inside `/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/lib/python3.11/site-packages/`.

---

## 10. Live-Server Evidence Required to Authorize Targeted Production Fix

To authorize and execute the targeted production fix with 100% confidence, the operator must provide:

1. **The last 25 lines of the live log file:**  
   `/home/powergri/repositories/pgcb-org-portal/services/api/passenger_startup.log`
2. **The exact Document Root path currently configured in cPanel Domains** for `api.powergriddiprocoush.org`.
3. **Confirmation whether `/home/powergri/repositories/pgcb-org-portal/services/api/.env` exists on the server.**

Once this evidence is retrieved, the exact failure line (e.g. `ValueError` vs `ImportError` vs `.htaccess` proxy error) will be definitively established, enabling an immediate, risk-free resolution.
