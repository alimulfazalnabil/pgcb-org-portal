# Phase 0.3 — HostSeba Repository Clone Verification Report

**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Target Environment:** HostSeba Shared Hosting / cPanel / CloudLinux / LiteSpeed Web Server / Phusion Passenger  
**Production API Domain:** `https://api.powergriddiprocoush.org`  
**GitHub Repository:** `https://github.com/alimulfazalnabil/pgcb-org-portal`  
**Local Repository:** `C:/Users/aflna/Downloads/pgcb-org-portal-v1.0`  
**Expected Server Repository Path:** `/home/powergri/repositories/pgcb-org-portal`  
**Expected Server API Path:** `/home/powergri/repositories/pgcb-org-portal/services/api`  
**Audit Date:** November 4, 2026  
**Investigation Mode:** Read-Only Verification (Findings classified as VERIFIED, NOT VERIFIED, or FAILED)

---

## 1. Access Limitations & Operating Boundary

* **Current Operating Environment:** Local developer workstation (Windows 11, `C:/Users/aflna/Downloads/pgcb-org-portal-v1.0`).
* **Server-Side Access Status:** **NO DIRECT ACCESS.**  
  The AI assistant operates strictly within this local directory and possesses no SSH key, terminal connection, web session, or API token to access the HostSeba hosting server or `/home/powergri/`.
* **Verification Boundary:**
  - **Local repository and GitHub remote repository:** `[VERIFIED]` through direct execution and Git network queries.
  - **HostSeba server filesystem and cPanel GUI configuration:** `[NOT VERIFIED]` from this terminal; must be inspected manually by the user/operator in cPanel.

---

## 2. Repository Existence & Git Status

| Check Item | Target Location | Status | Details / Evidence |
|---|---|---|---|
| **Local Working Tree** | `C:/Users/aflna/...` | **`[VERIFIED]`** | Branch `main`, HEAD commit `1a34625404abc662289454c515815e9da2d1693c`. Working tree is 100% clean. |
| **GitHub Remote** | `origin/main` | **`[VERIFIED]`** | Remote ref `refs/heads/main` points to `1a34625404abc662289454c515815e9da2d1693c` (confirmed via `git ls-remote`). |
| **HostSeba Directory** | `/home/powergri/repositories/pgcb-org-portal` | **`[NOT VERIFIED]`** | Requires operator terminal check (`ls -la /home/powergri/repositories/pgcb-org-portal`). |
| **HostSeba Git Tree** | `/home/powergri/repositories/pgcb-org-portal/.git` | **`[NOT VERIFIED]`** | Requires operator to run `git rev-parse HEAD` and `git status` inside `/home/powergri/repositories/pgcb-org-portal`. |

---

## 3. GitHub Commit Comparison

* **Local HEAD Commit:** [`1a34625404abc662289454c515815e9da2d1693c`](https://github.com/alimulfazalnabil/pgcb-org-portal/commit/1a34625) — `docs(audit): add Phase 0 deployment baseline and recovery checklist`
* **GitHub `main` Commit:** [`1a34625404abc662289454c515815e9da2d1693c`](https://github.com/alimulfazalnabil/pgcb-org-portal/commit/1a34625)
* **Sync Status:** **`[VERIFIED]` 100% Identical.** Zero commit divergence.
* **Server Expectation:** When cloned via `git clone -b main https://github.com/alimulfazalnabil/pgcb-org-portal.git`, the server checkout will match commit `1a34625`.

---

## 4. Required File Verification

Inspection of required application files in the codebase vs. server expectations:

| Relative Path | Local / GitHub Tree | HostSeba Server Status | Architectural Role & Server Risk |
|---|---|---|---|
| `services/api/passenger_wsgi.py` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Critical Entrypoint:** Adapts FastAPI via `a2wsgi` with auto-virtualenv discovery and credential-masked logging. |
| `services/api/requirements.txt` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Dependencies:** 18 packages (`fastapi>=0.115.0`, `psycopg[binary]>=3.2.6`, `a2wsgi>=1.10.7`). |
| `services/api/app/main.py` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Application:** FastAPI core application, lifespan handler, router definitions. |
| `services/api/alembic.ini` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Database Config:** Alembic migration settings and logging configuration. |
| `services/api/tmp/` | **`[FAILED / GAP]` (Missing)** | `[NOT VERIFIED]` | **CRITICAL RUNTIME GAP:** Empty directories are **not tracked by Git**. A fresh `git clone` will **not** contain `services/api/tmp/`. Any attempt to run `touch .../tmp/restart.txt` will fail with `No such file or directory` until `mkdir -p services/api/tmp` is executed. |
| `deployment/hostseba/api_subdomain_htaccess.example` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Directives:** LiteSpeed Passenger directives for `api.powergriddiprocoush.org/.htaccess`. |
| `deployment/hostseba/environment.example` | **`[VERIFIED]` (Exists)** | `[NOT VERIFIED]` | **Template:** Reference template for HostSeba production `.env` variables. |

---

## 5. Existing cPanel Application Configuration

Because direct cPanel API access is unavailable from this environment, the operator must verify the following reference settings in the cPanel GUI:

| Setting | Expected Value | Status | Risk / Mismatch Consideration |
|---|---|---|---|
| **cPanel Tool** | **Setup Python App** (CloudLinux) | `[NOT VERIFIED]` | Must use CloudLinux Setup Python App, not EasyApache 4 Application Manager. |
| **Application Root** | `repositories/pgcb-org-portal/services/api` | `[NOT VERIFIED]` | Must match the newly cloned path relative to `/home/powergri/`. |
| **Python Version** | `3.11` | `[NOT VERIFIED]` | Must point to `alt-python311`. |
| **Startup File** | `passenger_wsgi.py` | `[NOT VERIFIED]` | If set to `wsgi.py` or blank, Passenger may fail to find the entrypoint. |
| **Entry Point** | `application` | `[NOT VERIFIED]` | Must match `application = ASGIMiddleware(asgi_app)`. |
| **Virtual Environment Path** | `/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11` | `[NOT VERIFIED]` | Check whether virtualenv exists and contains pip packages (`a2wsgi`, `psycopg`). |
| **Application Manager** | **Disabled / Not Registered** | `[NOT VERIFIED]` | If also registered in Application Manager, Apache/LiteSpeed will encounter conflicting directives. |
| **Subdomain DocumentRoot** | `/home/powergri/api.powergriddiprocoush.org` | `[NOT VERIFIED]` | Must **not** be inside `/home/powergri/public_html/`. |

---

## 6. Production Storage & Configuration Status

| Component | Status | Security & Operational Reality |
|---|---|---|
| **Production `.env` File** | **`[NOT VERIFIED]` (High Danger)** | **Git does not track `.env`.** When the previous repository folder was deleted, `/home/powergri/repositories/pgcb-org-portal/services/api/.env` was **destroyed**. Re-cloning does **not** restore `.env`. Without manually recreating `.env`, the API **will fail immediately with HTTP 500** (`ValueError: JWT_SECRET...` and `ValueError: DATABASE_URL...`). |
| **cPanel GUI Variables** | **`[NOT VERIFIED]` (Unreliable)** | Under LiteSpeed Web Server, environment variables set via the cPanel GUI frequently fail to propagate to child WSGI workers. The physical file `services/api/.env` is strictly required. |
| **Uploads Directory** | **`[NOT VERIFIED]`** | If uploads were configured at `/home/powergri/pgcb_data/uploads`, they were preserved. If they were in `services/api/storage`, check backup `/home/powergri/pgcb-api-fix-backup-20261022-021936/`. |
| **Production PostgreSQL Database** | **`[NOT VERIFIED]`** | Database tables reside inside PostgreSQL daemon and were unaffected by repository deletion. Credentials must be re-entered into `.env`. |

---

## 7. Mismatches and Risks Summary

1. **`services/api/tmp/` Does Not Exist in Fresh Clones `[FAILED]`:**
   - Git does not track empty directories.
   - Touching `tmp/restart.txt` without first creating `services/api/tmp` will fail.
2. **Missing Production `.env` `[FAILED]`:**
   - Fresh Git checkout provides `.env.example`, but no active `.env`.
   - The application fail-fast mechanism strictly blocks startup if `DATABASE_URL` is SQLite or `JWT_SECRET` is missing.
3. **Uninstalled Dependencies `[NOT VERIFIED]`:**
   - If CloudLinux creates a fresh virtualenv upon re-registration, `fastapi`, `a2wsgi`, and `psycopg` will not be present until "Run Pip Install" is triggered.
4. **Stale Inode Caching `[RISK]`:**
   - LiteSpeed processes held open to the previous deleted directory must be terminated via `tmp/restart.txt` or cPanel Restart.

---

## 8. Exact Next Action for the Operator

Because server-side access is restricted to the operator, perform these exact non-destructive steps in cPanel:

### Step A: Verify Repository on HostSeba
In cPanel **Terminal**:
```bash
# 1. Check if repository directory exists
ls -ld /home/powergri/repositories/pgcb-org-portal

# 2. If already cloned, verify commit
cd /home/powergri/repositories/pgcb-org-portal
git rev-parse HEAD
# (Expected: 1a34625404abc662289454c515815e9da2d1693c)

# 3. If NOT yet cloned, perform clone now:
# cd /home/powergri/repositories
# git clone -b main https://github.com/alimulfazalnabil/pgcb-org-portal.git
```

### Step B: Create Required Runtime Directory
```bash
mkdir -p /home/powergri/repositories/pgcb-org-portal/services/api/tmp
```

### Step C: Re-create Production `.env`
In cPanel **File Manager**, create:
`/home/powergri/repositories/pgcb-org-portal/services/api/.env` (mode `0600`) with:
```dotenv
APP_ENV=production
DATABASE_URL=postgresql+psycopg://<db_user>:<encoded_password>@127.0.0.1:5432/<db_name>
JWT_SECRET=<32+_character_random_secret>
STORAGE_BACKEND=local
STORAGE_ROOT=/home/powergri/repositories/pgcb-org-portal/services/api/storage
CORS_ORIGINS=https://powergriddiprocoush.org,https://www.powergriddiprocoush.org
FRONTEND_URL=https://powergriddiprocoush.org
TRUSTED_PROXY_COUNT=1
```

### Step D: Re-install Dependencies in cPanel Setup Python App
1. Open cPanel → **Setup Python App**.
2. Select application for `api.powergriddiprocoush.org`.
3. Under **Configuration files**, enter `requirements.txt`.
4. Click **Run Pip Install**.
5. Click **Restart**.

### Step E: Test Verification Endpoint
```bash
curl -i https://api.powergriddiprocoush.org/live
```
*(Expected: `HTTP/1.1 200 OK` with `{"status":"alive"}`)*.
