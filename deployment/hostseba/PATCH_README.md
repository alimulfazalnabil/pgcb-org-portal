# Hostseba PGCB API Subdomain Fix — Patch Instructions

## 1. Overview
This patch resolves the server-level 404 issue on `https://api.powergriddiprocoush.org/health` by:
1. Providing the required LiteSpeed/CloudLinux Phusion Passenger directives in `.htaccess` for the API document root `/home/powergri/api.powergriddiprocoush.org/.htaccess`.
2. Removing invalid Apache mod_rewrite `[R=200]` syntax and avoiding duplicate CORS headers (allowing FastAPI's `CORSMiddleware` to handle CORS natively).
3. Hardening `services/api/passenger_wsgi.py` with explicit virtualenv auto-discovery (`/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11`), credential-masked error logging, and an emergency fallback WSGI handler returning HTTP 500 JSON instead of crashing silently.
4. Updating `apps/web/next.config.ts` and `apps/web/lib/api/client.ts` to target `https://api.powergriddiprocoush.org` in production while preserving `http://127.0.0.1:8000` for local development.

---

## 2. Pre-Installation Check & DocumentRoot Diagnostic
Execute this read-only test to verify which directory LiteSpeed is actually reading:
```bash
echo "NEW_ACTIVE_DOCROOT" > /home/powergri/api.powergriddiprocoush.org/probe.txt
echo "OLD_NESTED_DOCROOT" > /home/powergri/home/powergri/api.powergriddiprocoush.org/probe.txt
curl -i https://api.powergriddiprocoush.org/probe.txt
```
- If this returns `NEW_ACTIVE_DOCROOT` (HTTP 200), LiteSpeed is correctly reading the new document root.
- If this returns `OLD_NESTED_DOCROOT` (HTTP 200), LiteSpeed's vhost is still bound to the old directory.
- Verify your existing backup at `/home/powergri/pgcb-api-fix-backup-20261022-021936/`.
- Do NOT delete the old directory `/home/powergri/home/powergri/api.powergriddiprocoush.org` until the new document root is verified and working.

---

## 3. Installation Steps

### Step 1: Upload and Unpack Patch
Upload `hostseba-update-api-fix.zip` to `/home/powergri/repositories/pgcb-org-portal/` and extract:
```bash
cd /home/powergri/repositories/pgcb-org-portal
unzip -o hostseba-update-api-fix.zip
```

### Step 2: Install API DocumentRoot `.htaccess` in Both Target Locations
Because LiteSpeed's active VirtualHost might still point to the old nested directory pending an Apache configuration rebuild, deploy the `.htaccess` to **both** paths so Passenger engages regardless of vhost state:
```bash
# 1. Primary document root
cp /home/powergri/repositories/pgcb-org-portal/deployment/hostseba/api_subdomain_htaccess.example /home/powergri/api.powergriddiprocoush.org/.htaccess
chmod 644 /home/powergri/api.powergriddiprocoush.org/.htaccess

# 2. Nested document root (if it exists, bridge it so requests don't 404 while vhost updates)
if [ -d "/home/powergri/home/powergri/api.powergriddiprocoush.org" ]; then
    cp /home/powergri/repositories/pgcb-org-portal/deployment/hostseba/api_subdomain_htaccess.example /home/powergri/home/powergri/api.powergriddiprocoush.org/.htaccess
    chmod 644 /home/powergri/home/powergri/api.powergriddiprocoush.org/.htaccess
fi
```

### Step 3: Synchronize cPanel Python Selector & Restart App
1. Verify that `wsgi.py` and `passenger_wsgi.py` exist in `/home/powergri/repositories/pgcb-org-portal/services/api/`.
2. Log into cPanel and open **Setup Python App**.
3. Select the application for `api.powergriddiprocoush.org`.
4. Click **Save** to force CloudLinux and LiteSpeed to regenerate their application bindings.
5. Click **Restart** (or run `touch /home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt`).

---

## 4. Verification

Execute these verification commands from your terminal or browser:

```bash
# 1. Test API Liveness Probe (Should return HTTP 200 with JSON)
curl -i https://api.powergriddiprocoush.org/health

# 2. Test Alternative Liveness Probe
curl -i https://api.powergriddiprocoush.org/healthz

# 3. Test CORS Preflight Handled by FastAPI
curl -i -X OPTIONS https://api.powergriddiprocoush.org/api/v1/health \
  -H "Origin: https://powergriddiprocoush.org" \
  -H "Access-Control-Request-Method: GET"
```

Expected HTTP response for `/health`:
```http
HTTP/1.1 200 OK
Content-Type: application/json
...

{"status":"ok","database":"connected","service":"pgcb-api","version":"1.0.0-rc1","environment":"production"}
```

---

## 5. Rollback Steps

If unexpected issues occur:
```bash
# 1. Restore previous files from your timestamped backup
cp /home/powergri/pgcb-api-fix-backup-20261022-021936/passenger_wsgi.py /home/powergri/repositories/pgcb-org-portal/services/api/passenger_wsgi.py
cp /home/powergri/pgcb-api-fix-backup-20261022-021936/next.config.ts /home/powergri/repositories/pgcb-org-portal/apps/web/next.config.ts
cp /home/powergri/pgcb-api-fix-backup-20261022-021936/client.ts /home/powergri/repositories/pgcb-org-portal/apps/web/lib/api/client.ts

# 2. Restart Passenger
touch /home/powergri/repositories/pgcb-org-portal/services/api/tmp/restart.txt
```
