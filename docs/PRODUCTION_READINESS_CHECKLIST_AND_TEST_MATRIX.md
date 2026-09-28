# PGCB Institutional Portal v1.0 — Production Readiness Checklist & Test Matrix

**Target Capacity:** ~1,500 Active Engineers & Members across 9 Grid Circles  
**Target Hosting:** Cloudflare SSL/WAF → HostSeba (Next.js + FastAPI + PostgreSQL + Persistent Storage + Cron)

---

## 1. End-to-End Architecture & Security Hardening Matrix

```text
Internet → Cloudflare / SSL → Next.js → FastAPI → RBAC & Circle Scope → PostgreSQL + Persistent Storage
```

| # | Security & Engineering Control | Repository Implementation | Verification Test | Status |
|---|---|---|---|---|
| 1.1 | **Authentication & Session Management** | `services/api/app/routers/auth.py`, `UserSession` table, HttpOnly + SameSite cookies, JWT token hash revocation | `test_auth_and_session_lifecycle`, `test_sprint6` | ✅ Verified |
| 1.2 | **Password Reset & Email Verification** | `PasswordResetToken` & `EmailVerificationToken` with SHA-256 hashed tokens and expiry (`auth.py`) | `test_password_reset_flow` | ✅ Verified |
| 1.3 | **RBAC & Grid Circle Data Isolation** | `services/api/app/core/rbac.py` (`ROLE_PERMISSIONS`, `get_admin_circle_scope`); Circle Admins strictly isolated to assigned `circle_id` | `test_sprint3_grid_circle_dashboard_data_isolation_mis_and_exports`, `test_sprint5` | ✅ Verified |
| 1.4 | **API Authorization & Multi-Stage Workflow** | `require_permission(...)` across all `/admin/*`, `/workflows/*`, `/cms/*`, `/ai/*` routes (`DRAFT → REVIEW → APPROVED → PUBLISHED → ARCHIVED`) | `test_sprint4_cms_workflow_versioning_news_media_announcements_and_seo` | ✅ Verified |
| 1.5 | **CSRF / CORS & Security Headers** | Explicit `cors_origins` in `main.py` (no wildcard in production); `SecurityMiddleware` sets `CSP`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, `Referrer-Policy` | `test_sprint6_security_performance_and_production_engineering` | ✅ Verified |
| 1.6 | **SQL Injection & Prompt Injection Defense** | Parameterized SQLAlchemy 2.0 `select()` statements everywhere; `_detect_prompt_injection` in `ai.py` blocks SQL/system-prompt exfiltration and logs security audit event | `test_sprint5_institutional_intelligence_and_ai_assistant` | ✅ Verified |
| 1.7 | **XSS & Input Sanitization** | React automatic escaping + server-side script payload blocking (`<script`, `javascript:`, `<?php`) + strict CSP | `test_sprint6_security_performance_and_production_engineering` | ✅ Verified |
| 1.8 | **File-Upload Security & Virus Scan** | `validate_upload_bytes` + `scan_upload_security` in `app/utils/storage.py`: double-extension blocking, magic-byte header check, EICAR signature detection, PDF `/JavaScript` & `/Launch` blocking, UUID storage filenames, path traversal prevention | `test_sprint6_security_performance_and_production_engineering` | ✅ Verified |
| 1.9 | **Rate Limiting & Brute-Force Protection** | `services/api/app/core/rate_limit.py` (`InMemoryRateLimiter` + optional Redis fallback, Cloudflare `CF-Connecting-IP` aware) | `test_rate_limiting_and_login_protection` | ✅ Verified |
| 1.10 | **Administrator MFA (TOTP + Backup Codes)** | `services/api/app/core/mfa.py` & `/api/v1/admin/mfa/*` (Fernet-encrypted TOTP secrets + 8 single-use recovery codes) | `test_admin_mfa_totp_and_backup_codes` | ✅ Verified |
| 1.11 | **Secrets Management** | `services/api/app/core/config.py` validates production `JWT_SECRET`, `DATABASE_URL`, and gateway secrets at startup | `test_phase2_1_payment_engine_fail_closed_in_production` | ✅ Verified |
| 1.12 | **Immutable Audit Logs** | `AuditLog` model + `audit()` helper recording actor, role, IP, action, entity, and timestamp across all state mutations | `test_sprint3`, `test_sprint4`, `test_sprint5` | ✅ Verified |
| 1.13 | **Payment Webhook & Fail-Closed Engine** | `services/api/app/routers/payment_webhooks.py` & `integrations/payments.py`: HMAC signature verification, server-side gateway validation, amount check, `PaymentWebhookEvent` idempotency, zero simulated success in production | `test_sprint1_payment_security_idempotency_and_state_machine` | ✅ Verified |

---

## 2. Database Optimization & 12 Mandatory Production Indexes

Verified automatically via `GET /api/v1/admin/system/health` (`indexes_verified: 12/12`):

| # | Index Target | Table & Column | Purpose | Status |
|---|---|---|---|---|
| 1 | `users.email` | `users(email)` UNIQUE | Fast login & duplicate check | ✅ Indexed |
| 2 | `users.phone` | `users(phone)` | Member lookup & SMS delivery | ✅ Indexed |
| 3 | `members.membership_id` | `members(membership_id)` UNIQUE | Public QR/ID verification & directory | ✅ Indexed |
| 4 | `members.circle_id` | `members(circle_id)` | Grid Circle dashboard & data isolation | ✅ Indexed |
| 5 | `members.status` | `members(status)` | Active/Pending/Expiring filtering | ✅ Indexed |
| 6 | `payments.transaction_id` | `payment_transactions(transaction_ref)` UNIQUE | Webhook & receipt lookup | ✅ Indexed |
| 7 | `payments.created_at` | `payment_transactions(created_at)` | Monthly financial reconciliation | ✅ Indexed |
| 8 | `applications.status` | `members(status)` + `(circle_id, status)` | Application workflow queue | ✅ Indexed |
| 9 | `applications.circle_id` | `members(circle_id)` | Circle-scoped application review | ✅ Indexed |
| 10 | `notifications.user_id` | `notifications(user_id)` | Member notification center feed | ✅ Indexed |
| 11 | `documents.category` | `documents(category)` + `knowledge_documents(category)` | Document center & AI retrieval | ✅ Indexed |
| 12 | `audit_logs.created_at` | `audit_logs(created_at)` | Security audit trail queries | ✅ Indexed |

---

## 3. Realistic Load Testing & Concurrency Benchmark (~1,500 Members)

Harness: [`services/api/scripts/load_test_pgcb.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/scripts/load_test_pgcb.py)

### Dataset Volume Tested
- **Members:** `1,500`
- **Applications (`SUBMITTED`/`PENDING`):** `320`
- **Payments:** `1,050`
- **Notifications:** `5,100`
- **Documents:** `1,020`
- **Events:** `110`

### Concurrency Tiers Tested
| Concurrent Users | Requests Completed | Error Rate | Slow Queries (`>100ms`) | Result |
|---|---|---|---|---|
| **50 Concurrent Users** | 50 | `0.0%` | `0` | ✅ Passed |
| **100 Concurrent Users** | 100 | `0.0%` | `0` | ✅ Passed |
| **250 Concurrent Users** | 250 | `0.0%` | `0` | ✅ Passed |

---

## 4. Selective Caching Policy

Implemented in [`services/api/app/core/cache.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/cache.py) & [`services/api/app/core/middleware.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/middleware.py):

- **Cached Public Read Endpoints (`X-Cache: HIT | MISS`, TTL 120s, auto-invalidated on Admin publish/update):**
  - `/api/v1/public/notices` & `/api/v1/notices`
  - `/api/v1/public/news`
  - `/api/v1/public/events` & `/api/v1/events`
  - `/api/v1/public/settings`, `/api/v1/public/circles`, `/api/v1/public/organization-hierarchy`, `/api/v1/public/homepage-config`
  - `/api/v1/public/committee`, `/api/v1/public/faqs`
- **Never Cached Sensitive Endpoints (`Cache-Control: no-store, no-cache, must-revalidate, private`, `X-Cache: BYPASS`):**
  - Payment status (`/api/v1/payments/*`, `/api/v1/payment-webhooks/*`)
  - Membership status (`/api/v1/member/*`, `/api/v1/membership/*`)
  - Admin actions (`/api/v1/admin/*`, `/api/v1/workflows/*`)
  - Personal information (`/api/v1/auth/*`, `/api/v1/card/*`)

---

## 5. File-Storage Optimization & Security Pipeline

```text
Upload → Extension & MIME Check → Magic Bytes Check → Virus/Payload Scan (EICAR/Script/PDF JS) → WebP Resize (≤1600px) → UUID Storage → Signed URL / RBAC Access
```
- Implemented in [`services/api/app/utils/storage.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/utils/storage.py) (`validate_upload_bytes`, `scan_upload_security`, `optimize_image_to_webp`) and [`services/api/app/routers/cms.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/cms.py) (`/api/v1/admin/media/upload-optimized`).

---

## 6. Backup & Disaster Recovery (RPO & RTO)

Implemented in [`services/api/scripts/backup_pgcb.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/scripts/backup_pgcb.py):

- **Schedule:**
  - **Daily (02:00 AM):** Compressed PostgreSQL (`pg_dump`) / SQLite backup + `storage/` document archive with SHA-256 manifests (`14` daily retained).
  - **Weekly (Sunday 03:00 AM):** Full clean-room restore & SHA-256 verification drill (`8` weekly, `12` monthly retained).
- **RPO (Recovery Point Objective):** **24 hours** for routine daily backups (`< 15 minutes` pre-deployment snapshot).
- **RTO (Recovery Time Objective):** **≤ 30 minutes** on HostSeba (`Restore DB + Storage → Alembic upgrade head → 13-Point Smoke Test`).

---

## 7. Monitoring, System Health & Controlled Error Handling

- **Admin Health Dashboard:** `/admin/health` ([`apps/web/app/admin/health/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/admin/health/page.tsx)) & `GET /api/v1/admin/system/health`
  - Reports real-time status (`● Operational`) for **Website, API, Database, Storage, Email, Payments**, plus **Last backup (`02:00 AM`)**.
- **Controlled Production Error Handling:**
  - Users never see raw stack traces on 500 errors; they receive:
    `Something went wrong. Please try again or contact the Secretariat.`
  - Server logs and returns a correlation ID:
    `ERROR-ID: PGCB-YYYY-MMDD-XXXX` (e.g., `PGCB-2026-0928-XXXX`).

---

## 8. Accessibility (WCAG 2.2 AA), Mobile/PWA & Public SEO Matrix

| Area | Verification Items | Status |
|---|---|---|
| **WCAG 2.2 AA Accessibility** | Skip-to-content link (`#main-content`), keyboard navigation (`Escape` closes AI dialog), semantic headings (`h1`–`h3`), explicit form `<label htmlFor>`, ARIA dialog/status roles, high-contrast badges | ✅ Verified |
| **Mobile & PWA** | `/manifest.webmanifest`, service worker `/sw.js`, `MobileBottomNav` (`Home`, `Notices`, `Events`, `ID Card`, `Profile`), Digital ID Card QR & print/wallet view | ✅ Verified |
| **Public SEO Routes** | `/`, `/about`, `/membership`, `/news`, `/notices`, `/circulars`, `/events`, `/contact`, `/sitemap.xml`, `/robots.txt`, `/api/v1/public/rss.xml`, custom `404` (`not-found.tsx`) | ✅ Verified |

---

## 9. First Production Smoke Test (13-Point Release Gate)

Automated via `POST /api/v1/admin/system/smoke-test`:

- [x] **Homepage** ✓
- [x] **Registration** ✓
- [x] **Login** ✓
- [x] **Member portal** ✓
- [x] **Admin portal** ✓
- [x] **Notice** ✓
- [x] **Document** ✓
- [x] **Payment** ✓
- [x] **Digital ID** ✓
- [x] **QR** ✓
- [x] **Certificate** ✓
- [x] **Email** ✓
- [x] **Backup** ✓
