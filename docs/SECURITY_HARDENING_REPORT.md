# PGCB Organization Portal — Security Hardening Report
**Target Platform:** HostSeba Shared Hosting / cPanel / CloudLinux / Phusion Passenger  
**Production Release:** `v1.0.0-rc1`  
**Security Standard:** OWASP Top 10 + Institutional Data Protection Standard

---

## 1. Cryptography & Secret Protection

### 1.1 Secret Key Length & Complexity Enforcement
- **JWT_SECRET / SECRET_KEY:**
  - Evaluated at application startup via Pydantic model validator (`app.core.config.Settings.validate_production`).
  - Production and staging reject any placeholder secret starting with `dev-only-secret` or any secret shorter than 32 characters.
  - Startup fails immediately with an explicit `ValueError` if an insecure secret is detected.
- **Accidental Formatting Sanitization:**
  - `validate_production()` automatically strips accidental whitespace and surrounding single or double quotes (`'..."...`) that may be introduced during cPanel copy-paste.

### 1.2 Credential Masking in Telemetry & Logs
- All database connection strings, passwords, JWT tokens, SMTP credentials, and API secrets are dynamically scrubbed by `mask_sensitive_data()`:
  - Database URLs: `postgresql+psycopg://<CPANEL_DB_USER>:***@localhost:5432/<CPANEL_DB_NAME>`
  - Key-value pairs: `jwt_secret=***`, `password=***`, `token=***`
- Log files (`passenger_startup.log`, `migration_run.log`) and uncaught exception handlers never write raw credentials to disk or stderr.

### 1.3 MFA Encryption & Key Rotation
- MFA TOTP seeds are encrypted at rest using AES-128-CBC + HMAC-SHA256 authenticated encryption via `cryptography.fernet.Fernet`.
- **Key Rotation Fallback:** When a dedicated `MFA_ENCRYPTION_KEY` is configured, `decrypt_secret()` falls back to the legacy SHA-256 derived key if decryption with the primary key fails. This ensures zero user lockout during key rotation.
- Configured keys are strictly validated at startup to ensure compliance with 32-byte urlsafe base64 Fernet standards.

---

## 2. Authentication, Session & Access Control (RBAC)

### 2.1 Password Hashing
- User passwords are encrypted using **Argon2id** (`passlib.handlers.argon2`), the industry standard memory-hard hashing algorithm resistant to GPU cracking.

### 2.2 Session Security
- User session tokens are stored in HTTP-only cookies (`pgcb_access_token`):
  - `HttpOnly = True`: Prevents client-side JavaScript access and XSS token exfiltration.
  - `Secure = True`: Enforced in production; cookies are transmitted exclusively over encrypted HTTPS connections.
  - `SameSite = Lax`: Prevents ambient transmission on cross-origin requests.
  - Session revocation and expiration timestamps are tracked and enforced in `UserSession` database records.

### 2.3 Role-Based Access Control (RBAC) Matrix
The platform implements a strict 7-tier role hierarchy enforced at router endpoints via `require_roles`:
1. `SUPER_ADMIN`: Central administrative authority with universal bypass.
2. `CENTRAL_ADMIN`: Central office operations and secretariat management.
3. `CIRCLE_ADMIN`: Circle-specific operations (limited to their assigned geographical circle).
4. `FINANCE_ADMIN`: Payment tracking, transaction auditing, and financial receipts.
5. `OFFICE_SECRETARY`: Notice publication, member communications, and event management.
6. `MEMBER`: Authenticated PGCB engineer with access to their profile, digital card, certificates, and event registration.
7. `PUBLIC`: Unauthenticated visitors viewing public news, notices, and portal information.

---

## 3. Web Application Security: CORS & CSRF Defense

### 3.1 Strict CORS Origin Whitelisting
- Production explicitly whitelists trusted domains (`https://powergriddiprocoush.org`). Wildcard origins (`*`) and permissive regular expressions are strictly forbidden.
- Allowed headers explicitly include: `Content-Type`, `Authorization`, `X-Requested-With`, `X-Request-ID`, `X-CSRF-Token`, `Accept`.

### 3.2 Origin-Based CSRF Mitigation for Cookie Authentication
- In `app.core.middleware.SecurityMiddleware`:
  - For state-changing methods (`POST`, `PUT`, `PATCH`, `DELETE`), if a request carries the session cookie without a Bearer `Authorization` header, the request's `Origin` or `Referer` is validated against `get_allowed_origins()`.
  - Untrusted cross-site origins are rejected immediately with HTTP 403 Forbidden (`{"detail": "CSRF origin verification failed"}`).
  - Bearer token requests (used by mobile apps, background jobs, or explicit API clients) are not subject to ambient browser CSRF and proceed securely.

### 3.3 HTTP Security Headers
Applied globally to all HTTP responses via `_apply_security_headers`:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Prevents clickjacking attacks.
- `X-XSS-Protection: 1; mode=block`: Legacy browser filter protection.
- `Referrer-Policy: strict-origin-when-cross-origin`: Controls referrer leakage.
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`: Restricts sensitive browser APIs.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`: Enforces HTTPS for one year.
- `Content-Security-Policy`: Restricts resource execution to trusted self/HTTPS sources.

---

## 4. File Upload & Storage Security

### 4.1 Path Traversal Prevention
- `DiskStorageBackend._resolve_candidate()` verifies every file path using `Path.resolve()` and `candidate.relative_to(self.root_dir)`.
- Requests containing null bytes (`\x00`) or directory traversal components (`..`) raise an immediate `ValueError: Security: Path traversal attempt detected`.

### 4.2 Filename Sanitization
- `safe_name()` sanitizes filenames, stripping path separators and special characters, retaining only alphanumeric characters, dots, underscores, and dashes.

### 4.3 Outside-Web-Root Storage
- Storage is configured to `/home/powergri/storage`, located completely outside the web server's DocumentRoot (`/home/powergri/api.powergriddiprocoush.org` and `public_html`).
- Files can only be downloaded through authenticated FastAPI streaming endpoints with access control checks.

---

## 5. Database Safety & Integrity

### 5.1 Fail-Closed Database Guard
- `app.db.safety` prevents accidental execution of destructive operations (such as table drops, test truncations, or mock seeds) against production database instances or `pgcb_portal.db`.
- Rejects SQLite in production by default unless `ALLOW_SQLITE_IN_PRODUCTION=true` is explicitly configured.
