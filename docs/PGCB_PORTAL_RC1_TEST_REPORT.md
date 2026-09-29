# PGCB Organization Portal — Official RC1 Test Report (`v1.0.0-rc1`)

- **Repository**: `alimulfazalnabil/pgcb-org-portal`
- **Branch**: `release/v1.0.0-rc1` (synchronized with `develop/hostseba-production` and `main`)
- **Environment Mode**: `APP_ENV=staging` / Local RC1 Validation (`PAYMENT_MODE=sandbox`, `EMAIL_PROVIDER=console/test`, `STORAGE_BACKEND=local`)
- **Date**: 2026-09-29
- **Overall Gate Status**: **RC1 GREEN (`PASS`)**

---

## 1. Release Gate Summary

```text
╔══════════════════════════════╗
║       PGCB PORTAL RC1        ║
╠══════════════════════════════╣
║ Build                 PASS   ║
║ Database              PASS   ║
║ Authentication        PASS   ║
║ RBAC                  PASS   ║
║ Membership            PASS   ║
║ Admin workflow        PASS   ║
║ Payment sandbox       PASS   ║
║ Documents             PASS   ║
║ Digital ID            PASS   ║
║ QR verification       PASS   ║
║ Security              PASS   ║
║ E2E                   PASS   ║
║ Load test             PASS   ║
╚══════════════════════════════╝
```

| Release Criterion | Target | Actual | Status |
| :--- | :--- | :--- | :--- |
| **P0 issues** | `0` | `0` | ✅ PASS |
| **Critical security issues** | `0` | `0` | ✅ PASS |
| **Golden-path E2E** | `PASS` | `PASS` | ✅ PASS |
| **Database migration** | `PASS` | `PASS` (`20260301_0001` → `b72c9f4e8d11`) | ✅ PASS |
| **Payment sandbox** | `PASS` | `PASS` (Server pricing + HMAC + idempotent replay) | ✅ PASS |
| **RBAC** | `PASS` | `PASS` (7 roles + Circle Admin circle isolation) | ✅ PASS |
| **Production build** | `PASS` | `PASS` (Frontend TypeScript/Next.js + FastAPI boot) | ✅ PASS |
| **Backup restore** | `PASS` | `PASS` (`run_disaster_recovery_drill` < 1s) | ✅ PASS |

---

## 2. Category-by-Category Test Execution Matrix

| Category | What Was Tested | Verification Suite / Command | Result |
| :--- | :--- | :--- | :--- |
| **Build** | Frontend TypeScript/Next.js (`npx tsc --noEmit`) & Backend FastAPI application boot (`/health`, `/ready`) | `apps/web` TypeScript compiler + `tests/api/test_api_routes_and_health.py` | ✅ PASS |
| **Database** | All 21 core entities, Alembic head (`b72c9f4e8d11`), foreign keys, unique constraints (`email`, `membership_id`, `application_no`, `transaction_id`), transaction rollback atomicity | `tests/database/test_database_schema_and_integrity.py` | ✅ PASS |
| **Auth** | Registration, email verification, Argon2/Bcrypt login, `HttpOnly` cookie + JWT session validation, expired session rejection (`401`), password reset | `tests/unit/test_unit_domain_and_services.py` & `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **RBAC** | 7-role permission matrix (`SUPER_ADMIN`, `CENTRAL_ADMIN`, `MEMBERSHIP_ADMIN`, `FINANCE_ADMIN`, `CONTENT_ADMIN`, `CIRCLE_ADMIN`, `MEMBER`) + Circle Admin circle isolation (`403`) | `tests/auth/test_auth_and_6role_rbac.py` & `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **Membership** | 9-state lifecycle (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `CORRECTION_REQUIRED`, `APPROVED`, `PAYMENT_PENDING`, `ACTIVE`, `REJECTED`, `CANCELLED`) | `tests/unit/test_unit_domain_and_services.py` & `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **Documents** | Magic-byte & MIME validation (`PDF`/`JPG`/`PNG`), `5 MB` size cap, EICAR malware rejection, UUID storage outside public web root, authenticated owner/admin download | `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **Payment** | Server-authoritative pricing (`৳2,000`), sandbox simulation, HMAC webhook verification, idempotent replay protection, receipt PDF & QR verification | `tests/payments/test_payment_sandbox_and_webhooks.py` | ✅ PASS |
| **Digital ID** | Unique `PGD-YYYY-XXXX` / `PGCB-MEM-YYYY-XXXX` assignment on payment activation, digital ID card details, signed QR token | `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **QR Verification** | Public verification (`/api/v1/public/verify/{membership_id}` & `/api/v1/public/verify-token/{token}`), expired membership detection (`EXPIRED`), zero private PII leakage | `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **CMS** | `CONTENT_EDITOR` creates `DRAFT` (`403` on direct publish) → `CONTENT_ADMIN` reviews and publishes (`200`) → public feed updated + revision logged | `tests/api/test_api_routes_and_health.py::test_cms_create_review_publish_and_notifications` | ✅ PASS |
| **Notifications** | In-app notification creation on application submission, admin review, payment activation, and CMS notice publication | `tests/api/test_api_routes_and_health.py` & `tests/e2e/test_critical_member_workflow_e2e.py` | ✅ PASS |
| **Security** | IDOR/BOLA (`Member A -> Member B` returns `403/404`; `Circle Admin A -> Circle B` returns `403`), browser status/payment tamper (`403/400`), upload validation | `tests/e2e/test_critical_member_workflow_e2e.py::test_rc1_all_16_failure_paths_and_idor_bola_security` | ✅ PASS |
| **E2E** | Golden-path 15-step member & admin lifecycle from registration to active Digital ID and QR verification | `tests/e2e/test_critical_member_workflow_e2e.py::test_rc1_admin_membership_workflow_15_step_e2e` | ✅ PASS |
| **Performance** | Synthetic `1,500` members, `520` applications, `2,050` payments, `5,100` notifications, `1,020` documents, `10,000` audit logs + `50 / 100 / 250` concurrent users | `tests/database/test_database_schema_and_integrity.py::test_1500_member_capacity_and_250_user_concurrency` | ✅ PASS |
| **Backup** | Full database + storage backup archive creation, SHA-256 manifest verification, and clean restoration drill | `scripts/backup_pgcb.py` (`run_disaster_recovery_drill`) | ✅ PASS |

---

## 3. All 16 Failure Paths & IDOR/BOLA Security Verification

Tested in [`test_rc1_all_16_failure_paths_and_idor_bola_security`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/tests/e2e/test_critical_member_workflow_e2e.py#L418-L777):

| # | Failure / Attack Scenario | Endpoint / Mechanism | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Wrong password** | `POST /api/v1/auth/login` | `401 Unauthorized` | `401` | ✅ PASS |
| 2 | **Expired session** | `GET /api/v1/member/profile` (`expires_at < now`) | `401 Unauthorized` | `401` | ✅ PASS |
| 3 | **Duplicate email** | `POST /api/v1/auth/register` | `400 / 409` | `400` | ✅ PASS |
| 4 | **Duplicate membership** | Duplicate `employee_id` (`PATCH /profile`) & duplicate `POST /apply` when `ACTIVE` | `409 Conflict` | `409` | ✅ PASS |
| 5 | **Invalid document** | `POST /api/v1/member/documents` (`malware.exe` / bad magic bytes) | `400 Bad Request` | `400` | ✅ PASS |
| 6 | **Oversized document** | `POST /api/v1/member/documents` (`> 5 MB` payload) | `400 / 413` | `400` | ✅ PASS |
| 7 | **Unauthorized document access (IDOR)** | Member A requests `GET /api/v1/member/documents/{member_b_doc_id}/download` | `403 / 404` | `404` | ✅ PASS |
| 8 | **Unauthorized admin API** | Member A requests `GET /api/v1/admin/memberships/applications` | `403 Forbidden` | `403` | ✅ PASS |
| 9 | **Tampered payment amount** | Client sends `amount: 50` (`POST /member/payments`) or `amount: 10` (`POST /payments/sandbox/simulate`) | `400 Bad Request` | `400` | ✅ PASS |
| 10 | **Duplicate payment webhook** | Replay `POST /api/v1/payments/sandbox/simulate` for already-paid transaction | `200` (`idempotent_replay: true`) | `200` | ✅ PASS |
| 11 | **Failed payment** | Gateway returns `outcome: "FAILED"` | `payment_status: FAILED`, member stays `PAYMENT_PENDING` | Verified | ✅ PASS |
| 12 | **Rejected application** | Admin submits `REJECT` with `rejection_reason` | Status becomes `REJECTED` (`400` if reason omitted) | Verified | ✅ PASS |
| 13 | **Correction requested** | Admin submits `REQUEST_CORRECTION` with `correction_reason` | Status becomes `CORRECTION_REQUIRED` (`400` if reason omitted) | Verified | ✅ PASS |
| 14 | **Expired membership** | `GET /api/v1/public/verify/{membership_id}` when `validity_date < today` | `verified: false`, `status: "EXPIRED"` | Verified | ✅ PASS |
| 15 | **Revoked certificate** | `GET /api/v1/certificates/verify/{cert_no}` after revocation | `valid: false`, `revoked: true` | Verified | ✅ PASS |
| 16 | **Invalid QR** | `GET /api/v1/public/verify/PGD-INVALID-999999` & forged HMAC token | `404` / `400` | `404` / `400` | ✅ PASS |
| **IDOR-1** | **Member A → Member B Payment & Receipt** | Member A calls `/payments/sandbox/simulate` or `/member/payments/{b_id}/receipt` | `403 Forbidden` | `403` | ✅ PASS |
| **IDOR-2** | **Circle Admin A → Circle B Application** | Circle 1 Admin calls `GET` or `POST /action` on Circle 2 Member application | `403 Forbidden` | `403` | ✅ PASS |

---

## 4. P1 Issues Found & Fixed During RC1 Validation Sprint

1. **Document Upload Size Cap (`max_upload_mb`)**:
   - **Finding**: `Settings.max_upload_mb` defaulted to `10 MB` instead of the `5 MB` KYC document policy, allowing a `5.01 MB` PDF in the negative test.
   - **Fix**: Updated `max_upload_mb: int = 5` in [`services/api/app/core/config.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/config.py#L38). Verified `> 5 MB` uploads return `400 Bad Request`.
2. **Mandatory Reason Enforcement on `REQUEST_CORRECTION` and `REJECT`**:
   - **Finding**: `POST /api/v1/admin/memberships/applications/{member_id}/action` accepted `REQUEST_CORRECTION` without a reason note and used a fallback string instead of rejecting empty reasons.
   - **Fix**: Updated [`services/api/app/routers/admin.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/admin.py#L1182-L1194) to accept `note`, `correction_reason`, or `rejection_reason` and return `400 Bad Request` when omitted on `REQUEST_CORRECTION` or `REJECT`.
3. **Duplicate Employee ID Conflict Handling (`409 Conflict`)**:
   - **Finding**: Submitting an `employee_id` already claimed by another member needed an explicit pre-commit check in `PATCH /api/v1/member/profile`.
   - **Fix**: Added uniqueness check in [`services/api/app/routers/membership.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/membership.py#L522-L527) returning `409 Conflict`.
4. **Cross-Member Sandbox Payment Simulation & Expired QR Date Check**:
   - **Finding**: Added explicit ownership check (`403`) and `outcome: "FAILED"` support in [`services/api/app/routers/payments.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/payments.py#L749-L770), and date-based expiry check in [`services/api/app/routers/public.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/public.py#L115-L124).

---

## 5. Synthetic 1,500-Member Capacity & Concurrency Benchmark

Executed via [`scripts/load_test_pgcb.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/scripts/load_test_pgcb.py):

### 5.1 Dataset & Resource Metrics
| Metric | Target | Measured | Status |
| :--- | :--- | :--- | :--- |
| **Members (`users` + `members` + `memberships`)** | `1,500` | `1,500` | ✅ PASS |
| **Applications (`membership_applications`)** | `500` | `520` | ✅ PASS |
| **Payments (`payments` + `payment_transactions`)** | `2,000` | `2,050` | ✅ PASS |
| **Notifications (`notifications`)** | `5,000` | `5,100` | ✅ PASS |
| **Documents (`documents`)** | `1,000` | `1,020` | ✅ PASS |
| **Audit Records (`audit_logs`)** | `10,000` | `10,000` | ✅ PASS |
| **Database CPU Time** | `< 5,000 ms` | `2,390.62 ms` | ✅ PASS |
| **Peak RAM Usage** | `< 256 MB` | `5.63 MB` | ✅ PASS |
| **Database Disk Usage** | `< 50 MB` | `3.60 MB` | ✅ PASS |
| **Slow Queries (`> 100 ms`)** | `0` | `0` (`max = 17.34 ms`) | ✅ PASS |

### 5.2 Concurrency Tiers (`50`, `100`, `250` Concurrent Users)
| Concurrency Tier | Completed | Avg Response Time | p50 | p95 | p99 | Error Rate | Slow Requests (`> 500ms`) | Throughput |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **50 Concurrent Users** | `50 / 50` | `38.93 ms` | `31.76 ms` | `84.35 ms` | `101.35 ms` | `0.0%` | `0` | `261.2 req/s` |
| **100 Concurrent Users** | `100 / 100` | `54.28 ms` | `50.67 ms` | `142.25 ms` | `155.59 ms` | `0.0%` | `0` | `282.8 req/s` |
| **250 Concurrent Users** | `250 / 250` | `88.95 ms` | `75.57 ms` | `222.29 ms` | `245.31 ms` | `0.0%` | `0` | `274.4 req/s` |
