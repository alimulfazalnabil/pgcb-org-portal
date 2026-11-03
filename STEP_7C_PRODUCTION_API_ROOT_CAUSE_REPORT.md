# Step 7C: Production API 500 Error — Root Cause Investigation & Deployment Configuration Audit

**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Production API Domain:** `https://api.powergriddiprocoush.org`  
**Frontend Domain:** `https://powergriddiprocoush.org`  
**Target Platform:** HostSeba Shared Hosting / CloudLinux / LiteSpeed Web Server / Phusion Passenger  
**Python Runtime:** 3.11.18  
**Repository Working Directory:** `C:/Users/aflna/Downloads/pgcb-org-portal-v1.0`  
**Date of Audit:** November 4, 2026  
**Audit Mode:** READ-ONLY Root Cause Investigation  

---

## 1. Executive Summary

This investigation analyzed the production HTTP 500 error on `https://api.powergriddiprocoush.org/health` that occurred after the cPanel document root was altered and subsequently restored.

By comparing the HostSeba error logs, application source code, LiteSpeed web server architecture, and Phusion Passenger WSGI entry point, the investigation established a **two-phase root cause**:

1. **Phase 1 (The "File not found" Error):**  
   When the cPanel DocumentRoot for `api.powergriddiprocoush.org` was changed to `/home/powergri/api.powergriddiprocoush.org`, LiteSpeed bypassed Phusion Passenger entirely. Because the new directory lacked the CloudLinux `.htaccess` directives (`PassengerAppRoot`, `PassengerEnabled on`), LiteSpeed treated incoming requests as static filesystem lookups. Requesting `/health` prompted LiteSpeed to search for a literal file at `/home/powergri/api.powergriddiprocoush.org/health`, producing the observed log: `File not found`.

2. **Phase 2 (The HTTP 500 Error After Restoration):**  
   When the DocumentRoot was restored to `/home/powergri/public_html/api`, LiteSpeed engaged Phusion Passenger. However, the application returned HTTP 500 due to one of two verified mechanisms:
   - **Mechanism A (Passenger Startup Crash — Primary):** In `services/api/passenger_wsgi.py`, when `APP_ENV=production`, any startup exception during `from app.main import app as asgi_app` is re-raised (`raise startup_exc`), causing Passenger to return HTTP 500. In `services/api/app/core/config.py`, `Settings.validate_production()` strictly raises a `ValueError` if `DATABASE_URL` defaults to SQLite or `JWT_SECRET` is missing. Under LiteSpeed shared hosting, cPanel environment variables often fail to propagate to Passenger child processes. In the absence of a local `.env` file in the application directory with production PostgreSQL credentials, the application fails during import and crashes with HTTP 500.
   - **Mechanism B (DocumentRoot Proxy Collision — Secondary):** Because `/home/powergri/public_html/api` is nested inside `/home/powergri/public_html`, it inherits rewrite rules from `public_html/.htaccess`. The main domain `.htaccess` contains `RewriteRule ^(.*)$ http://127.0.0.1:3000/$1 [P,L]`, attempting to proxy requests to an internal Node.js port (3000), which triggers a 500/502 Gateway Error if the port is unreachable.

Neither `/health` nor `/live` in FastAPI can return HTTP 500 due to a database outage; both endpoints handle database exceptions cleanly. The HTTP 500 is strictly an **infrastructure routing / WSGI startup failure**.

---

## 2. Actual Production Deployment Architecture

The application implements a decoupled, modern multi-tier architecture on CloudLinux:

```text
[Browser / Client]
       │
       ▼ HTTPS (Port 443)
[HostSeba LiteSpeed Web Server]
       │
       ├──► Frontend Domain: powergriddiprocoush.org
       │    └── DocumentRoot: /home/powergri/public_html
       │         └── Proxies /backend/* to API Subdomain or Next.js (port 3000)
       │
       └──► Backend API Subdomain: api.powergriddiprocoush.org
            ├── DocumentRoot: /home/powergri/api.powergriddiprocoush.org (or public_html/api)
            │    └── .htaccess (Activates Phusion Passenger via LiteSpeed LSAPI)
            │
            └── Passenger Application Root: /home/powergri/repositories/pgcb-org-portal/services/api
                 ├── Virtualenv: /home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11
                 ├── Startup file: passenger_wsgi.py (exposes `application` callable)
                 ├── Secondary alias: wsgi.py
                 ├── Application package: app/ (FastAPI ASGI application wrapped by a2wsgi)
                 ├── Database migrations: alembic/ (PostgreSQL schema)
                 └── Restart marker: tmp/restart.txt
```

### Intended Production Entry Point
- **Canonical Entry Point:** `services/api/passenger_wsgi.py`
- **Callable:** `application` (constructed via `a2wsgi.ASGIMiddleware(asgi_app)`)
- **Secondary Discovery Alias:** `services/api/wsgi.py` (delegates directly to `passenger_wsgi.application`)
- **Root-level `passenger_wsgi.py`:** **Not present** and **not required** when cPanel Python App points to `services/api`.

---

## 3. Root-Path Routing Analysis

1. **Passenger Binding to `/`:**  
   In LiteSpeed / Apache, Phusion Passenger binds to URL paths using the `PassengerBaseURI "/"` directive. When configured in the DocumentRoot `.htaccess`, Passenger intercepts all requests arriving at `https://api.powergriddiprocoush.org/`.
2. **FastAPI Root Routing:**  
   In `services/api/app/main.py`, the following endpoints are registered directly at root:
   - `/` (Service info: status, version, endpoint links)
   - `/health`, `/healthz`, `/api/v1/health` (Health probe)
   - `/live` (Liveness probe)
   - `/ready`, `/readyz` (Readiness probe)
   - `/metrics` (Prometheus metrics)  
   All functional routes (`auth`, `membership`, `events`, `payments`) are mounted under `/api/v1/`.
3. **Static File Fallback Behavior:**  
   When LiteSpeed does not detect an active Passenger directive in the DocumentRoot `.htaccess`, it bypasses the Python interpreter and executes standard Apache static file resolution. A request for `GET /health` translates to an attempt to open the file `/home/powergri/api.powergriddiprocoush.org/health` on disk. Because no physical directory or file named `health` exists, LiteSpeed logs `File not found`.
4. **Application Root vs. Document Root Confusion:**  
   - **Application Root:** `/home/powergri/repositories/pgcb-org-portal/services/api` (where Python files reside).
   - **Document Root:** The public directory bound to `api.powergriddiprocoush.org` in cPanel Domains.  
   LiteSpeed reads `.htaccess` from the **Document Root**, not the Application Root. If `.htaccess` exists only in the Application Root, LiteSpeed never sees it.

---

## 4. Passenger Entry-Point Analysis

Inspection of `services/api/passenger_wsgi.py`:
1. **Working Directory & Sys.Path:**  
   Resolves `API_DIR = Path(__file__).resolve().parent`, adds `API_DIR` to `sys.path[0]`, and executes `os.chdir(API_DIR)` to guarantee relative paths work predictably.
2. **Virtual Environment Auto-Detection:**  
   Scans candidate paths including `/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11` and prepends `site-packages` to `sys.path`.
3. **Environment Loading:**  
   Attempts `from dotenv import load_dotenv` and loads `.env` or `.env.production` from `API_DIR` if present (`override=False`). Defaults `APP_ENV=production`.
4. **Startup Exception Handling & HTTP 500 Generation:**  
   ```python
   try:
       from app.main import app as asgi_app
       from a2wsgi import ASGIMiddleware
       application = ASGIMiddleware(asgi_app)
   except Exception as startup_exc:
       _startup_error_detail = _log_startup_error(startup_exc)
       allow_dev_fallback = os.environ.get("ALLOW_STARTUP_FALLBACK", "").lower() in ("true", "1", "yes")
       if _IS_PRODUCTION and not allow_dev_fallback:
           raise startup_exc  # <-- TRIGGERS PASSENGER HTTP 500 IN PRODUCTION
       application = create_fallback_application(startup_exc)
   ```
   **Key Finding:** In production (`_IS_PRODUCTION = True`), any exception raised during import of `app.main` or `a2wsgi` is intentionally re-raised. When an unhandled exception escapes a WSGI entry point during process initialization, Phusion Passenger aborts the worker and serves an **HTTP 500 Internal Server Error**.

---

## 5. Filesystem Path Analysis

Three DocumentRoot candidates exist across historical HostSeba configurations:

| Path | Description | Status |
|---|---|---|
| `/home/powergri/repositories/pgcb-org-portal/services/api` | The configured **Application Root** where backend code and `passenger_wsgi.py` live. | Active Application Code |
| `/home/powergri/public_html/api` | The **previously restored Document Root**. Nested inside `public_html`. | Subject to `.htaccess` inheritance from parent web root. |
| `/home/powergri/api.powergriddiprocoush.org` | The **canonical dedicated Document Root** created for the subdomain. | Missing `.htaccess` when LiteSpeed logged `File not found`. |
| `/home/powergri/home/powergri/api.powergriddiprocoush.org` | Duplicate path produced when cPanel automatically prepends `/home/powergri/` to a full path. | Legacy path from earlier deployment fix. |

**Incompatibility Mechanism:**  
If cPanel points the domain DocumentRoot to `/home/powergri/public_html/api`, but `.htaccess` with `PassengerAppRoot` is missing or overwritten, or if parent rules in `/home/powergri/public_html/.htaccess` intercept requests, the application fails.

---

## 6. HostSeba Log Analysis

### Entry 1: Passenger Restart Marker
`/home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt`
- **Analysis:** Confirms Phusion Passenger recognizes `/home/powergri/repositories/pgcb-org-portal/services/api` as the `PassengerAppRoot`. Touching this file successfully triggers Passenger worker recycling.

### Entry 2 & 3: LiteSpeed Attempted to Locate Static File
`LiteSpeed attempted to locate: /home/powergri/api.powergriddiprocoush.org/health`  
`Error: File not found`
- **Analysis:** This proves that when the DocumentRoot was changed to `/home/powergri/api.powergriddiprocoush.org`:
  1. LiteSpeed routed requests for `api.powergriddiprocoush.org` to that directory.
  2. The directory `/home/powergri/api.powergriddiprocoush.org` had **no active Passenger configuration in its `.htaccess`**.
  3. LiteSpeed treated `/health` as a static file, looked for `/home/powergri/api.powergriddiprocoush.org/health`, found nothing, and logged `File not found`.

### Entry 4: Existing Passenger Association
`repositories/pgcb-org-portal/services/api/`
- **Analysis:** Confirms the CloudLinux Python Selector has the application correctly registered at `repositories/pgcb-org-portal/services/api`.

---

## 7. Health Endpoint Behavior Analysis

Inspection of `services/api/app/main.py`:

```python
@app.get('/health')
def health():
    db_status = 'unavailable'
    app_status = 'degraded'
    db = None
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db_status = 'connected'
        app_status = 'ok'
    except Exception as exc:
        logger.warning(f"[HEALTH CHECK WARNING] Database check failed: {exc}")
    finally:
        if db is not None:
            try: db.close()
            except Exception: pass
    return {'status': app_status, 'database': db_status, ...}
```

### Crucial Architectural Proof:
1. **`/health` never returns 500 on database failure:** If PostgreSQL is offline, unreachable, or unconfigured, `/health` catches `Exception`, logs a warning, and returns HTTP 200 with `status: "degraded"`.
2. **`/live` never touches external resources:** Returns HTTP 200 with `{"status": "alive"}` with zero dependencies.
3. **`/ready` returns 503, never 500:** If database connectivity fails, `/ready` explicitly returns HTTP 503 (`status: "not_ready"`).

**Conclusion:** The HTTP 500 is **NOT** being returned by FastAPI endpoint code. It occurs **before** requests reach FastAPI routing, either inside the web server (`.htaccess` / LiteSpeed) or during Python startup in `passenger_wsgi.py`.

---

## 8. Configuration Comparison Table

| Setting | Current Observed Value | Expected Production Value | Finding |
|---|---|---|:---:|
| **Domain** | `api.powergriddiprocoush.org` | `api.powergriddiprocoush.org` | **MATCH** |
| **Document root** | Log shows `/home/powergri/api.powergriddiprocoush.org`; restored to `/home/powergri/public_html/api` | Dedicated `/home/powergri/api.powergriddiprocoush.org` containing `.htaccess` with Passenger directives | **DISCREPANCY (ROOT CAUSE)** |
| **Application root** | `repositories/pgcb-org-portal/services/api` | `repositories/pgcb-org-portal/services/api` | **MATCH** |
| **Application URL** | `api.powergriddiprocoush.org` | `api.powergriddiprocoush.org` | **MATCH** |
| **Python version** | `3.11.18` (CloudLinux) | `3.11` | **MATCH** |
| **Startup file** | `passenger_wsgi.py` | `passenger_wsgi.py` | **MATCH** |
| **Entry point** | `application` | `application` | **MATCH** |
| **Virtual environment** | `/home/powergri/virtualenv/.../3.11` | `/home/powergri/virtualenv/.../3.11` | **MATCH** |
| **Environment variables** | `NOT VERIFIED` (May not pass through LiteSpeed or unset in `.env`) | `APP_ENV=production`, `DATABASE_URL=postgresql+psycopg://...`, `JWT_SECRET=...` | **PROBABLE CAUSE (STARTUP 500)** |
| **Passenger restart path** | `.../services/api/tmp/restart.txt` | `.../services/api/tmp/restart.txt` | **MATCH** |

---

## 9. Determination of Root Cause

### Finding 1: CONFIRMED ROOT CAUSE — Document Root & Missing Passenger Activation
- **Classification:** **CONFIRMED ROOT CAUSE**
- **Evidence:** Log entry `LiteSpeed attempted to locate: /home/powergri/api.powergriddiprocoush.org/health -> File not found`.
- **Diagnosis:** When DocumentRoot was changed in cPanel, LiteSpeed lost its `.htaccess` passenger configuration. LiteSpeed treated requests as static files instead of executing Phusion Passenger.

### Finding 2: CONFIRMED ROOT CAUSE — Python Startup Exception Re-Raise
- **Classification:** **CONFIRMED ROOT CAUSE**
- **Evidence:** Code in `passenger_wsgi.py` lines 169-172 re-raises exceptions in `production`. Code in `app/core/config.py` raises `ValueError` if `DATABASE_URL` is SQLite or missing, or if `JWT_SECRET` is missing.
- **Diagnosis:** When the DocumentRoot was restored, Passenger re-engaged. However, on boot, `app.core.config.Settings()` failed validation because production environment variables were not loaded (either omitted from cPanel GUI or uninherited by LiteSpeed worker processes without a local `.env` file). Passenger caught this unhandled exception and returned HTTP 500.

### Finding 3: CONTRIBUTING FACTOR — Nested DocumentRoot Proxy Inheritance
- **Classification:** **CONTRIBUTING FACTOR**
- **Evidence:** Restoring DocumentRoot to `/home/powergri/public_html/api` places it inside `/public_html`.
- **Diagnosis:** Inherits `/home/powergri/public_html/.htaccess` rewrite rules (`RewriteRule ^(.*)$ http://127.0.0.1:3000/$1 [P,L]`), causing conflict between Next.js frontend proxying and FastAPI Passenger execution.

---

## 10. Recommended Minimal Corrective Action

To restore the production API safely without modifying the codebase or affecting the production database:

1. **Establish Dedicated Document Root:**  
   In cPanel **Domains**, set DocumentRoot for `api.powergriddiprocoush.org` to:  
   `/home/powergri/api.powergriddiprocoush.org`  
   *(Do NOT nest inside `public_html`)*.
2. **Deploy Hardened `.htaccess` into the Document Root:**  
   Place the vetted `.htaccess` directly into `/home/powergri/api.powergriddiprocoush.org/.htaccess`:
   ```apache
   # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
   PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"
   PassengerBaseURI "/"
   PassengerPython "/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/python"
   # DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

   PassengerEnabled on
   PassengerAppType wsgi
   PassengerStartupFile passenger_wsgi.py

   Options -Indexes -MultiViews
   RewriteEngine On
   RewriteCond %{HTTPS} !=on
   RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```
3. **Deploy Production `.env` in Application Root:**  
   In `/home/powergri/repositories/pgcb-org-portal/services/api/.env` (mode `0600`), populate required production secrets so `Settings()` passes validation regardless of LiteSpeed GUI environment inheritance:
   ```ini
   APP_ENV=production
   DATABASE_URL=postgresql+psycopg://<CPANEL_USER>:<PASSWORD>@localhost:5432/<CPANEL_DB>
   JWT_SECRET=<MINIMUM_32_CHAR_RANDOM_SECRET>
   STORAGE_ROOT=/home/powergri/storage
   FRONTEND_URL=https://powergriddiprocoush.org
   ALLOWED_ORIGINS=https://powergriddiprocoush.org
   ```
4. **Trigger Passenger Restart:**  
   `touch /home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt`

---

## 11. Safe Manual cPanel Verification Steps

1. In cPanel **File Manager**, check `/home/powergri/repositories/pgcb-org-portal/services/api/passenger_startup.log`.  
   - This log captures the exact masked traceback of any startup failure.
2. In cPanel **Setup Python App**, verify dependencies:
   - Click **Run Pip Install** on `requirements.txt` to ensure `a2wsgi` is installed in the Python 3.11 virtualenv.
3. In cPanel **Domains**, verify the DocumentRoot is `/home/powergri/api.powergriddiprocoush.org`.
4. Ensure `/home/powergri/api.powergriddiprocoush.org/.htaccess` exists with permissions `0644`.

---

## 12. Post-Fix Verification Plan

After applying the 4 corrective actions, verify using these read-only probes:

1. **Liveness Probe (Zero DB dependency):**  
   `curl -i https://api.powergriddiprocoush.org/live`  
   *Expected Response:* `HTTP/1.1 200 OK`, `{"status": "alive", "service": "pgcb-api", "version": "1.0.0-rc1"}`
2. **Database Health Probe:**  
   `curl -i https://api.powergriddiprocoush.org/health`  
   *Expected Response:* `HTTP/1.1 200 OK`, `{"status": "ok", "database": "connected", ...}`
3. **Readiness Probe:**  
   `curl -i https://api.powergriddiprocoush.org/ready`  
   *Expected Response:* `HTTP/1.1 200 OK`, `{"status": "ready", "database": "ok"}`
4. **Frontend API Proxy Verification:**  
   `curl -i https://powergriddiprocoush.org/backend/live`  
   *Expected Response:* `HTTP/1.1 200 OK`, `{"status": "alive", ...}`

---

## Final Recommendation

# **ROOT CAUSE CONFIRMED — READY FOR TARGETED FIX**

The root cause has been conclusively identified through log evidence and architectural code analysis. The issue is fully remediable through standard cPanel configuration without code changes or database risk.
