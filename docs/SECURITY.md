# PGCB Organization Portal — Security Architecture

## 1. Authentication & Session Security

- **Password Hashing**: Passwords are hashed using cryptographic salted hashing (`hash_password` / `verify_password` in `app/core/security.py`) and never stored or logged in plaintext.
- **Dual Transport Auth**: Supports `HttpOnly`, `SameSite=Lax`, `Secure` (in production) session cookies (`pgcb_access_token`) as well as `Authorization: Bearer <token>` headers for API clients.
- **CSRF Protection**: State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) authenticated via cookies are validated against the `pgcb_csrf_token` cookie and `X-CSRF-Token` header in `SecurityMiddleware`.
- **Administrator MFA (TOTP)**: Administrators can enable RFC 6238 Time-based One-Time Password (TOTP) MFA (`/api/v1/admin/mfa/setup`, `/enable`, `/disable`). TOTP secrets are encrypted at rest using Fernet (`mfa_secret_enc`).

---

## 2. Role-Based Access Control (RBAC)

All administrative and member endpoints enforce server-side authorization via `require_permission('<scope>')` in `app/core/rbac.py`. Client-side visibility (`PermissionGate` and `AdminSidebar`) is strictly a UX convenience; every API endpoint independently validates the caller's JWT/session and role permissions.

---

## 3. Cryptographic Verification (Member Cards & Certificates)

- **Digital Member ID Cards**: Signed using HMAC-SHA256 (`SECRET_KEY`) over the member's `membership_id` and expiration timestamp (`app/utils/qr_card.py`). Tampering with any character of the QR token invalidates the signature (`400 Invalid or expired verification token`).
- **Digital Certificates**: Each issued certificate receives a unique serial number (`PGCB-CERT-YYYY-XXXXXXXX`) and a SHA-256 verification token hash stored in the database (`verification_token_hash`). Revoked certificates immediately return `REVOKED` status upon public verification.
- **Privacy-Safe Public Verification**: Public verification endpoints (`/api/v1/public/verify/*` and `/api/v1/certificates/verify/*`) return only institutional credential metadata (Name, Membership ID, Designation, Circle, Status, Issue/Validity Date) and never expose private PII such as NID numbers, residential addresses, personal phone numbers, or emails.

---

## 4. Upload Security & Rate Limiting

- **File Uploads**: Restricted to explicit MIME allowlists (`application/pdf`, `image/jpeg`, `image/png`, `image/webp`, `video/mp4`) and read in bounded chunks with a strict 10 MB cap (`HTTP 413` on overflow). Filenames are sanitized via `_safe_name()` and resolved against `STORAGE_ROOT` to prevent path traversal.
- **Security Headers & Request Tracing**: `SecurityMiddleware` attaches a unique `X-Request-ID` to every response and sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Structured Error Envelope**: All HTTP exceptions return a consistent JSON structure containing both backward-compatible `detail` and structured `error: { code, message, request_id }` without leaking stack traces.
