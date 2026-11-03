# PGCB Organization Portal — Production Smoke Test Runbook
**Target Subdomain:** `https://api.powergriddiprocoush.org`  
**Frontend Domain:** `https://powergriddiprocoush.org`  
**Target Environment:** HostSeba cPanel / LiteSpeed / Phusion Passenger  
**Release:** `v1.0.0-rc1`

This document details the complete post-deployment verification procedure to confirm that all services, routes, database connections, and security controls are operating correctly in production.

---

## 1. Automated Health & Readiness Verifications

Run these `curl` commands from your local workstation or browser:

### 1.1 Process Liveness Probe
```bash
curl -i -s https://api.powergriddiprocoush.org/live
```
- **Expected Status:** `HTTP/2 200`
- **Expected JSON:**
  ```json
  {
    "status": "alive",
    "service": "pgcb-api",
    "version": "1.0.0-rc1"
  }
  ```

### 1.2 Truthful Health Check
```bash
curl -i -s https://api.powergriddiprocoush.org/health
```
- **Expected Status:** `HTTP/2 200`
- **Expected JSON:**
  ```json
  {
    "status": "ok",
    "database": "connected",
    "service": "pgcb-api",
    "version": "1.0.0-rc1",
    "environment": "production"
  }
  ```
  *(Note: If the database is disconnected, this endpoint truthfully reports `"status": "degraded"`, `"database": "unavailable"`)*.

### 1.3 Readiness Probe
```bash
curl -i -s https://api.powergriddiprocoush.org/ready
```
- **Expected Status:** `HTTP/2 200`
- **Expected JSON:**
  ```json
  {
    "status": "ready",
    "database": "ok"
  }
  ```

### 1.4 OpenAPI / Swagger UI
Open in your browser:
```text
https://api.powergriddiprocoush.org/docs
```
- **Expected:** Interactive Swagger UI loads, displaying all versioned endpoints (`/api/v1/auth`, `/api/v1/public`, `/api/v1/member`, `/api/v1/admin`, `/api/v1/events`, etc.).

---

## 2. Security Headers & CORS Smoke Test

### 2.1 Security Headers Inspection
```bash
curl -I https://api.powergriddiprocoush.org/health
```
- **Required Headers to Verify:**
  - `x-content-type-options: nosniff`
  - `x-frame-options: DENY`
  - `referrer-policy: strict-origin-when-cross-origin`
  - `server-timing: app;dur=...`

### 2.2 CORS Preflight Test
```bash
curl -i -X OPTIONS https://api.powergriddiprocoush.org/api/v1/auth/login \
  -H "Origin: https://powergriddiprocoush.org" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization, X-CSRF-Token"
```
- **Expected Status:** `HTTP/2 200`
- **Expected Headers:**
  - `access-control-allow-origin: https://powergriddiprocoush.org`
  - `access-control-allow-credentials: true`

---

## 3. Core Workflow Functional Smoke Tests

### 3.1 Public Content Routes
```bash
# Verify public notices
curl -i -s https://api.powergriddiprocoush.org/api/v1/public/notices

# Verify public news
curl -i -s https://api.powergriddiprocoush.org/api/v1/public/news

# Verify executive committee listing
curl -i -s https://api.powergriddiprocoush.org/api/v1/public/committee
```
- **Expected Status:** `HTTP/2 200` with JSON arrays.

### 3.2 Authentication & Session Verification
1. Login as Super Admin:
   ```bash
   curl -i -s -X POST https://api.powergriddiprocoush.org/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -H "Origin: https://powergriddiprocoush.org" \
     -d '{"email": "secretariat@powergriddiprocoush.org", "password": "YourStrongAdminPassword123!"}'
   ```
   - **Expected Status:** `HTTP/2 200`
   - **Expected Response:** JSON with `access_token` and `Set-Cookie: pgcb_access_token=...; HttpOnly; Secure; SameSite=lax`.

2. Query Profile using Bearer Token:
   ```bash
   curl -i -s https://api.powergriddiprocoush.org/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```
   - **Expected Status:** `HTTP/2 200`
   - **Expected JSON:** User profile with `role: "SUPER_ADMIN"`.

### 3.3 CSRF Protection Verification
Attempt a cross-site mutation with session cookie and untrusted origin:
```bash
curl -i -s -X POST https://api.powergriddiprocoush.org/api/v1/auth/logout \
  -H "Cookie: pgcb_access_token=<valid_or_dummy_cookie>" \
  -H "Origin: https://malicious-website.com"
```
- **Expected Status:** `HTTP/2 403 Forbidden`
- **Expected JSON:** `{"detail": "CSRF origin verification failed"}`

---

## 4. Verification Checklist Sign-off

| Check Item | Endpoint / Action | Pass Criteria | Status |
| :--- | :--- | :--- | :---: |
| Process Liveness | `GET /live` | Status 200, `status: alive` | [ ] |
| Database Health | `GET /health` | Status 200, `database: connected` | [ ] |
| API Readiness | `GET /ready` | Status 200, `database: ok` | [ ] |
| Security Headers | `GET /health` | `nosniff`, `DENY` present | [ ] |
| CORS Preflight | `OPTIONS /api/v1/auth/login` | Allowed origin returned | [ ] |
| CSRF Origin Check | `POST /api/v1/auth/logout` | 403 on untrusted origin | [ ] |
| Public CMS | `GET /api/v1/public/notices` | Status 200 JSON list | [ ] |
| Admin Authentication | `POST /api/v1/auth/login` | Status 200 + JWT cookie | [ ] |
| File Storage Root | `/home/powergri/storage` | Folders exist, 755 perms | [ ] |
| Alembic Migrations | `scripts/run_migrations.py` | Schema at HEAD | [ ] |
