# Phase 0: Non-Destructive Recovery Checklist

**Project:** PGCB Organization Portal (`pgcb-org-portal`)  
**Production API:** `https://api.powergriddiprocoush.org`  
**Hosting Environment:** HostSeba Shared Hosting / cPanel / CloudLinux / LiteSpeed / Phusion Passenger  
**Objective:** Restore production API availability without deleting, rebuilding, or resetting existing application assets.

---

## 1. Safety Rules & Operational Constraints

1. **DO NOT DELETE THE APPLICATION DIRECTORY:** Keep `/home/powergri/repositories/pgcb-org-portal` intact.
2. **DO NOT DELETE OR REBUILD THE VIRTUALENV:** Keep `/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11` intact.
3. **DO NOT RUN REMOTE DATABASE MIGRATIONS:** Do not execute `alembic upgrade head` until the API is booting and connection strings are verified.
4. **DO NOT COMMIT OR PUSH:** Local Git repository remains locked in read-only audit mode.
5. **DO NOT LOG OR EXPOSE SECRETS:** Ensure database passwords and JWT secrets are kept confidential.

---

## 2. Evidence Collection Checklist (Operator Step 1)

Before changing any settings, obtain these three pieces of live evidence via cPanel:

- [ ] **Check 1: Retrieve Live Server Traceback**
  - Path: `/home/powergri/repositories/pgcb-org-portal/services/api/passenger_startup.log` (or `stderr.log`).
  - Action: View the file in cPanel File Manager and copy the bottom 30 lines.
  - Expected Insight: Identifies the exact exception causing HTTP 500 (e.g. `ModuleNotFoundError: No module named 'a2wsgi'`, `ValueError: JWT_SECRET is missing...`, or `ValueError: DATABASE_URL cannot be SQLite...`).

- [ ] **Check 2: Confirm Subdomain DocumentRoot**
  - Location: cPanel **Domains** (or **Subdomains**).
  - Action: Inspect the Document Root listed for `api.powergriddiprocoush.org`.
  - Verification:
    - PASS: `/home/powergri/api.powergriddiprocoush.org`
    - FAIL: `/home/powergri/public_html/api` (causes proxy loop / 500 with Next.js)
    - FAIL: `/home/powergri/home/powergri/api.powergriddiprocoush.org` (nested double path)

- [ ] **Check 3: Inspect Server `.env` File Presence & Permissions**
  - Path: `/home/powergri/repositories/pgcb-org-portal/services/api/.env`
  - Action: Check whether this file exists in cPanel File Manager (enable "Show Hidden Files" in Settings).
  - Verification:
    - Does it exist? (Yes / No)
    - Permissions: `0600` (readable only by user `powergri`)
    - Does it define `APP_ENV=production`?
    - Does it define `DATABASE_URL=postgresql+psycopg://...`?
    - Does it define `JWT_SECRET` ($\ge 32$ random characters)?

---

## 3. Targeted Non-Destructive Remediation (Operator Step 2)

Depending on the evidence gathered above, apply the minimal required adjustment:

### Action Path A: If Error is `ValueError: JWT_SECRET...` or `ValueError: DATABASE_URL...`
Because LiteSpeed does not reliably propagate cPanel GUI environment variables:
1. Open cPanel File Manager.
2. Navigate to `/home/powergri/repositories/pgcb-org-portal/services/api/`.
3. If `.env` does not exist, create it (or copy from `deployment/hostseba/environment.example`).
4. Set permissions to `0600`.
5. Populate valid production credentials:
   ```dotenv
   APP_ENV=production
   DATABASE_URL=postgresql+psycopg://powergri_user:PASSWORD@127.0.0.1:5432/powergri_dbname
   JWT_SECRET=USE_A_STRONG_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
   STORAGE_BACKEND=local
   STORAGE_ROOT=/home/powergri/repositories/pgcb-org-portal/services/api/storage
   CORS_ORIGINS=https://powergriddiprocoush.org,https://www.powergriddiprocoush.org
   FRONTEND_URL=https://powergriddiprocoush.org
   ```

### Action Path B: If Error is `ModuleNotFoundError: No module named 'a2wsgi'` (or `fastapi`)
1. In cPanel, navigate to **Setup Python App**.
2. Select the application for `api.powergriddiprocoush.org`.
3. Under **Configuration files**, enter `requirements.txt`.
4. Click **Run Pip Install**.
5. Wait for the confirmation notice indicating all 18 dependencies installed successfully.

### Action Path C: If DocumentRoot is Incorrect or Missing `.htaccess`
1. If DocumentRoot in cPanel **Domains** is nested or inside `public_html`, change it to:
   ```text
   /home/powergri/api.powergriddiprocoush.org
   ```
2. Verify that `/home/powergri/api.powergriddiprocoush.org/.htaccess` exists with permissions `0644` containing:
   ```apache
   PassengerAppRoot "/home/powergri/repositories/pgcb-org-portal/services/api"
   PassengerBaseURI "/"
   PassengerPython "/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11/bin/python"
   PassengerEnabled on
   PassengerAppType wsgi
   PassengerStartupFile passenger_wsgi.py
   Options -Indexes -MultiViews
   ```

---

## 4. Non-Destructive Application Restart (Operator Step 3)

To reload Passenger workers without terminating the process manager or losing uptime:

```bash
touch /home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt
```
*(Or in cPanel Setup Python App, click the **Restart** button).*

---

## 5. Post-Remediation Verification Protocol (Operator Step 4)

Test the endpoints in order:

### Test 1: Liveness Probe (Zero Dependencies)
```bash
curl -i https://api.powergriddiprocoush.org/live
```
* **Expected Result:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json
  
  {"status":"alive"}
  ```
* **Significance:** Proves that Phusion Passenger, Python 3.11, `a2wsgi`, and FastAPI are booting and serving requests normally.

### Test 2: Health Probe (Database Connection Check)
```bash
curl -i https://api.powergriddiprocoush.org/health
```
* **Expected Result:**
  ```http
  HTTP/1.1 200 OK
  Content-Type: application/json
  
  {"status":"ok","database":"connected","service":"pgcb-api","version":"1.0.0-rc1","environment":"production"}
  ```
* **Significance:** Proves that the PostgreSQL connection string is valid and database connectivity is operational.

### Test 3: CORS Preflight
```bash
curl -i -X OPTIONS https://api.powergriddiprocoush.org/api/v1/health \
  -H "Origin: https://powergriddiprocoush.org" \
  -H "Access-Control-Request-Method: GET"
```
* **Expected Result:**
  ```http
  HTTP/1.1 200 OK
  Access-Control-Allow-Origin: https://powergriddiprocoush.org
  Access-Control-Allow-Credentials: true
  ```

---

## 6. Non-Destructive Rollback Protocol

If remediation yields unexpected behavior:
1. Revert `/home/powergri/api.powergriddiprocoush.org/.htaccess` to previous version.
2. Confirm the timestamped backup at `/home/powergri/pgcb-api-fix-backup-20261022-021936/` is available for reference.
3. Touch `/home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt`.
4. Do NOT drop database tables or delete the repository.
