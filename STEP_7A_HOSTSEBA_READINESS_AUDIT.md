# Step 7A: Final HostSeba Deployment Readiness Audit

**Repository:** `C:/Users/aflna/Downloads/pgcb-org-portal-v1.0`  
**Target Platform:** HostSeba Shared Hosting / CloudLinux / Phusion Passenger / LiteSpeed / Python 3.11 / PostgreSQL  
**Subdomains:**  
- Backend API: `https://api.powergriddiprocoush.org`  
- Frontend Portal: `https://powergriddiprocoush.org`  
**Approved Release Candidate Archive:** `dist/hostseba-pgcb-api-v1.0.0-final.zip`  
**Expected SHA-256:** `5b05454cc09faaf820c284edb779b9f218dbb59f518e1ab1deaabb71b82024d3`  
**Audit Date:** November 3, 2026  

---

## 1. Audit Matrix & Findings Classification

| # | Audit Item | Finding Classification | Summary / Verification Evidence |
|---|---|:---:|---|
| **1** | **Archive Checksum and Size** | **PASS** | Size: `324,840` bytes. SHA-256 matches expected `5b05454cc09faaf820c284edb779b9f218dbb59f518e1ab1deaabb71b82024d3` exactly. Byte-level integrity confirmed. |
| **2** | **Passenger WSGI & a2wsgi** | **PASS** | `passenger_wsgi.py` exposes `application` callable wrapping FastAPI via `a2wsgi.ASGIMiddleware`. `requirements.txt` pins `a2wsgi>=1.10.7`. Fail-fast on production startup exceptions verified. |
| **3** | **Python 3.11 Compatibility** | **PASS** | All dependencies declare modern versions compatible with Python 3.11. Uses `psycopg[binary]>=3.2.6` (eliminates C-compiler/libpq build requirements on shared hosting). |
| **4** | **cPanel Guide vs Archive Structure** | **WARNING** | Guide accurately matches archive layout (`alembic/`, `app/`, `passenger_wsgi.py`, `scripts/`). **Warning:** Guide suggests testing `https://api.powergriddiprocoush.org/docs`, but Swagger UI is intentionally disabled (`docs_url=None`) in production mode for security. Operators must expect HTTP 404 on `/docs`. |
| **5** | **PostgreSQL Connection & URL Encoding** | **PASS** | Connection URL uses `postgresql+psycopg://`. `app/core/config.py` automatically normalizes legacy drivers and auto-encodes passwords when `db_host`/`db_user`/`db_password` are provided via `quote_plus`. Documentation clearly guides percent-encoding in complete URLs. |
| **6** | **Migration Runner & Alembic Chain** | **PASS** | `scripts/run_migrations.py` tested and operational. Masks passwords in logs/tracebacks. Unconditionally rejects SQLite in production/staging. Discovers all 14 sequential Alembic revisions to head `e8f4a1b9c321` (v15). |
| **7** | **Environment Variables Reference** | **PASS** | `docs/ENVIRONMENT_VARIABLES_REFERENCE.md` documents all core backend and frontend environment variables with production examples and constraints. |
| **8** | **Admin Bootstrap & Security** | **PASS** | `app/scripts/create_admin.py` enforces minimum 12 chars in production, rejects placeholder emails and known weak passwords. Preserves existing password on rerun unless explicitly requested. |
| **9** | **Storage Permissions & Init** | **PASS** | Persistent storage root `/home/powergri/storage` is outside public web root. `DiskStorageBackend` creates `documents/` and `member_documents/` with `0750` permissions and canary write verification. |
| **10** | **HostSeba-Specific Assumptions** | **NOT VERIFIED** | Requires live cPanel interaction: local PostgreSQL server socket/TCP availability, outbound pip connectivity for wheel installation, cPanel UI script execution feature, LiteSpeed Passenger environment variable inheritance. |
| **11** | **Blockers Before Staging** | **PASS** | Zero code, packaging, dependency, or security blockers identified. |
| **12** | **Archive Unchanged Confirmation** | **PASS** | Candidate archive `dist/hostseba-pgcb-api-v1.0.0-final.zip` remained completely untouched and byte-identical throughout all audit steps. |

---

## 2. Detailed Findings

### Item 1 — Archive Checksum and Size
- **File:** `dist/hostseba-pgcb-api-v1.0.0-final.zip`
- **File Size:** `324,840` bytes
- **SHA-256 Checksum:** `5b05454cc09faaf820c284edb779b9f218dbb59f518e1ab1deaabb71b82024d3`
- **Preserved Archive:** `dist/hostseba-pgcb-api-v1.0.0-step6o-preserved.zip` (`320,644` bytes, SHA-256: `c13a1164a79af98dc6a55ea48a36a70596bbed1f3aae5149da19ee319c25bfaf`)
- **Status:** **PASS**

### Item 2 — Passenger WSGI Entrypoint and a2wsgi Dependency
- `passenger_wsgi.py` in the archive implements:
  - Dynamic `sys.path` bootstrapping for CloudLinux virtualenv directory structures.
  - Fail-fast re-raising of startup exceptions in `APP_ENV=production`.
  - Sensitive credential masking in logs and tracebacks (`passenger_startup.log` and `sys.stderr`).
  - Import of `a2wsgi.ASGIMiddleware` wrapping `app.main.asgi_app`.
- `requirements.txt` contains `a2wsgi>=1.10.7`.
- Isolated invocation test returned HTTP 200 OK across WSGI protocol.
- **Status:** **PASS**

### Item 3 — Python 3.11 Compatibility from Dependencies
- Packages declared in `requirements.txt`:
  - `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0`, `sqlalchemy>=2.0.30`, `psycopg[binary]>=3.2.6`, `pydantic-settings>=2.8.0`, `PyJWT>=2.10.0`, `python-jose[cryptography]>=3.3.0`, `passlib[argon2]>=1.7.4`, `argon2-cffi>=23.1.0`, `email-validator>=2.2.0`, `python-multipart>=0.0.20`, `alembic>=1.15.0`, `httpx>=0.28.0`, `pytest>=8.0.0`, `qrcode>=8.0`, `Pillow>=10.4.0`, `cryptography>=43.0.0`, `a2wsgi>=1.10.7`.
- All packages provide official pre-built Linux x86_64 wheels for Python 3.11.
- Crucially, `psycopg[binary]` provides bundled libpq C-libraries, eliminating compiler toolchain requirements on shared hosting.
- **Status:** **PASS**

### Item 4 — cPanel Deployment Guide vs Archive Structure
- The directory layout in `docs/HOSTSEBA_DEPLOYMENT_GUIDE.md` matches the archive:
  - `alembic/` (with 14 revisions in `versions/`)
  - `alembic.ini`
  - `app/` (including `app/storage/`, `app/scripts/create_admin.py`, `app/main.py`)
  - `passenger_wsgi.py` & `wsgi.py`
  - `requirements.txt`
  - `scripts/run_migrations.py`, `scripts/backup_pgcb.py`, `scripts/verify_production_contract.py`
  - `api_subdomain_htaccess.example`
- **Warning Identified:** Line 170-171 of `HOSTSEBA_DEPLOYMENT_GUIDE.md` lists `https://api.powergriddiprocoush.org/docs` as a post-deployment verification check. However, in `APP_ENV=production` or `staging`, `docs_url`, `redoc_url`, and `openapi_url` are disabled (`None`) by security hardening design. Visiting `/docs` in production returns HTTP 404.
- **Status:** **WARNING** (Documentation note only; does not block deployment).

### Item 5 — PostgreSQL Connection & URL Encoding Guidance
- Psycopg 3 dialect: `postgresql+psycopg://` is enforced.
- Config validator auto-converts `postgres://`, `postgresql://`, and `postgresql+psycopg2://` prefixes.
- Auto-encoding: If credentials are provided via discrete variables (`DB_USER`, `DB_PASSWORD`), `quote_plus` automatically handles special characters.
- If passed as a single `DATABASE_URL`, `docs/HOSTSEBA_DEPLOYMENT_GUIDE.md` explicitly notes that passwords with special characters must be percent-encoded.
- **Status:** **PASS**

### Item 6 — Migration Runner and Alembic Revision Chain
- `scripts/run_migrations.py`:
  - Contains credential masking (`mask_sensitive`) for URIs, query params, and tokens.
  - Unconditionally blocks SQLite if `APP_ENV` is `production` or `staging`.
  - Discovers the full revision DAG: 14 versions from `bca12bda0867` (base) to `e8f4a1b9c321` (v15 head).
  - Single head, linear revision path, zero branch splits.
- **Status:** **PASS**

### Item 7 — Environment Variables Documentation
- `docs/ENVIRONMENT_VARIABLES_REFERENCE.md` documents all required and optional variables for both backend API and frontend Next.js application.
- Includes operational parameters (`APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, `MFA_ENCRYPTION_KEY`, `STORAGE_ROOT`, `FRONTEND_URL`, `COOKIE_NAME`, `RATE_LIMIT_ENABLED`, `SMTP_*`, `BKASH_*`, `SSLCOMMERZ_*`).
- **Status:** **PASS**

### Item 8 — Admin Bootstrap Instructions & Security Requirements
- `app/scripts/create_admin.py` enforces:
  - Minimum 12-character password in production.
  - Rejection of passwords in `UNSAFE_PASSWORDS` dictionary.
  - Rejection of placeholder email domains (`@example.com`, `@pgcb.org.bd.example`).
  - Idempotency: preserves existing password on repeat runs unless `--reset-password` / `RESET_ADMIN_PASSWORD=true` is set.
  - Password is never echoed to logs or console output.
- **Status:** **PASS**

### Item 9 — Upload & Storage Directory Permissions
- Storage path: `/home/powergri/storage` outside the web root (`public_html` and `api.powergriddiprocoush.org`).
- Permissions: `0750` (read/write/execute for owner, read/execute for group, zero access for others).
- `DiskStorageBackend.ensure_root_exists()` automatically initializes `documents` and `member_documents` subdirectories.
- Canary write test `.write_test` verifies write capability on application boot.
- **Status:** **PASS**

### Item 10 — HostSeba-Specific Unverified Assumptions
The following assumptions cannot be verified locally and must be validated upon initial connection to HostSeba:
1. **Local PostgreSQL Socket/TCP Access:** Whether HostSeba's PostgreSQL server accepts local connections on `localhost:5432` or requires a specific Unix domain socket path. *(Status: NOT VERIFIED)*
2. **Pip Outbound Internet Connectivity:** Whether the CloudLinux Python Selector "Run Pip Install" has outbound network access to PyPI on this specific account/cluster. *(Status: NOT VERIFIED)*
3. **cPanel "Execute python script" UI Availability:** Whether the cPanel theme on HostSeba exposes the script execution box under "Setup Python App" or requires invoking scripts via cron/ssh. *(Status: NOT VERIFIED)*
4. **LiteSpeed Passenger Environment Variables:** Whether environment variables set via cPanel GUI are fully inherited by child worker processes under LiteSpeed. (Mitigated by fallback `.env` loading in `passenger_wsgi.py`). *(Status: NOT VERIFIED)*
- **Status:** **NOT VERIFIED**

### Item 11 — Pre-Staging Blockers
- **Critical Code Blockers:** 0
- **Packaging Blockers:** 0
- **Security Blockers:** 0
- **Database Schema Blockers:** 0
- **Status:** **PASS**

### Item 12 — Release Archive Integrity Confirmation
- Re-verified archive checksum after all checks:
  - `dist/hostseba-pgcb-api-v1.0.0-final.zip`
  - SHA-256: `5b05454cc09faaf820c284edb779b9f218dbb59f518e1ab1deaabb71b82024d3`
- Unchanged and verified byte-for-byte.
- **Status:** **PASS**

---

## 3. Final Recommendation

# **READY FOR STAGING**

The candidate release package **`dist/hostseba-pgcb-api-v1.0.0-final.zip`** meets all deployment invariants, passes isolated execution verification, and contains hardened operational safeguards. It is ready for upload and staged deployment to HostSeba shared hosting following the cPanel deployment guide.

*(Safety Confirmation: No live systems were accessed, no files uploaded, no remote databases modified, and no Git commits or pushes executed.)*
