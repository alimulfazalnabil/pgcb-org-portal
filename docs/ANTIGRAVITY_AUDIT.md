# PGCB Diploma Engineers Organization Portal — Master Antigravity Audit (`Stage 1: Phase 0–4`)

- **Repository**: `alimulfazalnabil/pgcb-org-portal`
- **Audit Branch**: `production-completion` (based on `52d1458`)
- **Audit Date**: September 29, 2026
- **Stage Scope**: Stage 1 (Phase 0–4 Audit Only — Zero Application Code Modifications)

---

## 1. Executive Summary & Overall Completion State

The PGCB Diploma Engineers Organization Portal (`ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি`) is a full-stack institutional web platform comprising a **Next.js 15.5 (React 19 / TypeScript 5.8 / Tailwind CSS 3.4)** frontend in [`apps/web/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web) and a **FastAPI / SQLAlchemy 2.0 / Alembic** backend in [`services/api/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api).

| Subsystem | Completion | Status | Summary |
| :--- | :---: | :---: | :--- |
| **Database & Migrations** | **94%** | ✅ Working / 🟡 Dual Tables | 47 SQLAlchemy tables across [`core.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/models/core.py) & [`payments.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/models/payments.py); 13 Alembic migrations (`head = b72c9f4e8d11`); official 1,457-member dataset (`2026–2028` term across 20 Grid Circles) extracted and ready in [`services/api/data/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/data). |
| **Authentication & 6-Role RBAC** | **95%** | ✅ Working | Argon2id password hashing, JWT + `HttpOnly` cookie session tracking (`user_sessions`), email verification, password reset tokens, admin TOTP MFA (`pyotp` + Fernet encryption), and 6-role RBAC (`SUPER_ADMIN`, `CENTRAL_ADMIN`, `CIRCLE_ADMIN`, `AUDITOR`, `MEMBER`, `APPLICANT`). |
| **Membership & Admin Review Lifecycle** | **93%** | ✅ Working | Public & member application submission, draft saving, document upload (`NID`, `CERTIFICATE`, `PHOTO`), application tracking (`/membership/track`), admin review desk (`/admin/memberships/applications`), circle-scoped filtering, and bulk CSV import wizard. |
| **Payment Sandbox & Live Gateways** | **92%** | ✅ Working | Sandbox simulation, manual bank/challan verification, bKash Tokenized Checkout (`_grant_token`, `create`, `execute`, `status`), Nagad checkout initialization, SSLCommerz integration, idempotent webhook processing, and signed PDF receipt generation. |
| **Digital ID Card, Certificates & QR Verification** | **95%** | ✅ Working | CR80 front/back PNG & print-ready PDF ID cards, HMAC-SHA256 signed QR tokens, public verification (`/verify`, `/member/verify/[membership_id]`, `/certificate/[token]`), and member certificate wallet. |
| **Public Website & Visual Parity** | **82%** | 🟡 Mixed UI | Core pages (`/`, `/about`, `/leadership`, `/members`, `/membership/*`, `/verify`, `/notices`, `/circulars`, `/news`, `/documents`, `/search`) use modern Tailwind UI. Older public routes (`/committee`, `/circles`, `/circles/[slug]`, `/events`, `/journal`, `/media`, `/contact`, `/privacy`, `/terms`, `/accessibility`) still use legacy CSS classes or contain hardcoded demo text. |
| **Admin Console & CMS** | **90%** | ✅ Working | 25 admin routes covering overview KPIs, applications, member directory, CSV import/export, events, attendance QR check-in, payments, certificates, notices, documents, circulars, journal, media, committee/CMS, RBAC roles/permissions, reports, audit logs, AI intelligence, and settings. |
| **Deployment & DevOps** | **85%** | 🟡 Needs `render.yaml` | `docker-compose.yml`, `docker-compose.prod.yml`, and HostSeba deployment scripts exist; root `render.yaml` Blueprint for Render multi-service deployment is not yet committed. |

---

## 2. Phase 0 — Repository & Architecture Inventory

### 2.1 Frontend Architecture ([`apps/web/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web))
- **Framework**: Next.js `^15.5.15` (App Router located directly under [`apps/web/app/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app), **not** `apps/web/src/app/`).
- **Language & Styling**: TypeScript `5.8.3`, Tailwind CSS `3.4.17` + global stylesheet [`apps/web/app/globals.css`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/globals.css).
- **API Client**: Centralized typed client in [`apps/web/lib/api.ts`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/lib/api.ts) routing requests through Next.js rewrite proxy `/backend/api/v1/*` configured in [`apps/web/next.config.mjs`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/next.config.mjs).
- **Shared Components ([`apps/web/components/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components))**:
  - Layout & Navigation: [`Header.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/Header.tsx), [`Footer.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/Footer.tsx), [`MobileBottomNav.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/MobileBottomNav.tsx), [`HelpdeskWidget.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/HelpdeskWidget.tsx)
  - Domain Components: [`MemberDataTable.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/MemberDataTable.tsx), [`NoticeList.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/NoticeList.tsx), [`SectionHead.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/SectionHead.tsx)
  - Admin Shell: [`AdminHeader.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/admin/AdminHeader.tsx), [`AdminSidebar.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/admin/AdminSidebar.tsx), [`PermissionGate.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/admin/PermissionGate.tsx), [`StatusBadge.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/admin/StatusBadge.tsx)
  - UI Primitives: [`EmptyState.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/EmptyState.tsx), [`ErrorState.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/ErrorState.tsx), [`LoadingState.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/LoadingState.tsx), [`Modal.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/Modal.tsx), [`Pagination.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/Pagination.tsx), [`Toast.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/components/ui/Toast.tsx)

### 2.2 Backend Architecture ([`services/api/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api))
- **Entry Point**: [`services/api/app/main.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/main.py) mounting 16 routers under `/api/v1` plus `/`, `/health`, `/api/v1/health`, `/live`, `/ready`, and `/metrics`.
- **Core Infrastructure ([`services/api/app/core/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core))**:
  - [`config.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/config.py): Pydantic Settings with production validation (`JWT_SECRET` length & non-default check, PostgreSQL URL normalization to `postgresql+psycopg://`, persistent disk path `/var/data/uploads`).
  - [`security.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/security.py): Argon2 password hashing, JWT creation/decoding, HMAC-SHA256 QR verification token signing & validation.
  - [`deps.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/deps.py): Session/cookie + Bearer JWT authentication dependencies (`get_current_user`, `require_admin`, `require_super_admin`, `require_secretariat_or_admin`, `require_finance_access`).
  - [`permissions.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/permissions.py) & [`rbac.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/rbac.py): Fine-grained permission matrix and role normalization across the 6 institutional roles.
  - [`middleware.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/middleware.py) & [`rate_limit.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/rate_limit.py): Security headers (`CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`), request ID correlation, structured error IDs (`PGCB-YYYY-MMDD-XXXX`), and sliding-window rate limiting (in-memory + Redis).
  - [`uploads.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/uploads.py): Magic-byte file signature inspection (`%PDF-`, PNG, JPEG, WEBP), path traversal protection, UUID storage filenames, and size enforcement.
  - [`mfa.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/mfa.py): TOTP MFA secret encryption at rest and backup code verification.
- **Storage Layer ([`services/api/app/storage/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/storage))**:
  - [`local_storage.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/storage/local_storage.py) supporting local dev (`./storage`) and Render/HostSeba persistent disk (`/var/data/uploads`) with segregated `public/` and `private/` subdirectories.
- **Service Layer ([`services/api/app/services/`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services))**:
  - [`card_generator.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services/card_generator.py): High-resolution Pillow CR80 ID card front/back PNG & PDF generator.
  - [`certificate_service.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services/certificate_service.py): Membership and event certificate PNG/PDF generator with embedded verification QR codes.
  - [`receipt_service.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services/receipt_service.py): Official payment receipt PDF generator (`PGCB-RCP-YYYY-XXXXXX`) with cryptographic verification token.
  - [`knowledge_service.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services/knowledge_service.py): Document chunking, hybrid BM25/TF-IDF + optional OpenAI `text-embedding-3-small` vector search, and `gpt-4o-mini` RAG synthesis with deterministic fallback.
  - [`notification_service.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/services/notification_service.py): Multi-channel (`IN_APP`, `EMAIL`, `SMS`) notification queue and SMTP/Console delivery worker.

---

## 3. Phase 4 — Content & Data-Driven Architecture Audit

### 3.1 What MUST Be CMS / Database Driven vs. Currently Hardcoded

| Page / Component | Current Source | Audit Finding | Action Required in Stage 2/3 |
| :--- | :--- | :--- | :--- |
| **Homepage Counters (`/`)** | `GET /api/v1/public/stats` | ✅ **Dynamic** (`stats.active_members`, `stats.active_circles`, `stats.publications`, `stats.upcoming_events`). | Seed official 1,457 members & 20 circles so live counters reflect real numbers (`১,৪৫৭ জন`, `২০ টি`). |
| **Homepage Urgent Notice Bar (`Header.tsx`)** | `GET /api/v1/notices/urgent` | ✅ **Dynamic** (only renders when an active urgent notice exists). | None — already CMS-driven. |
| **Homepage Utility Bar (`Header.tsx`)** | `GET /api/v1/public/settings` | ✅ **Dynamic** with sensible fallback defaults (`contact_phone`, `contact_email`, `address_bn`). | Make `Footer.tsx` also consume `public/settings` so footer contact details are not static. |
| **Homepage President's Message (`/`)** | `GET /api/v1/public/committee` | ✅ **Dynamic** (selects committee member whose `designation_bn` contains `সভাপতি`). | Ensure Central Committee seed/CMS data has official text or clean empty state. |
| **Committee Message Page (`/committee/message`)** | Hardcoded JSX in [`committee/message/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/committee/message/page.tsx#L23) | ❌ **Hardcoded Demo Name** (`প্রকৌশলী মোঃ আব্দুর রহমান`). | Replace hardcoded name/message with dynamic fetch from `GET /api/v1/public/committee` + `GET /api/v1/public/settings` with clean fallback. |
| **Central & Circle Leadership (`/leadership` vs `/committee`)** | `GET /api/v1/public/committee` & `/circles/{id}/committee` | 🟡 **Duplicate Routes**: `/leadership` is modern Tailwind; `/committee` is legacy 3-line JSX with `"IDEB ORGANIZATIONAL STRUCTURE"` eyebrow. | Upgrade `/committee` to use the unified modern layout or redirect/unify with `/leadership`. |
| **Grid Circles List (`/circles`)** | `GET /api/v1/public/circles` | 🟡 **Outdated Eyebrow & Styling**: [`circles/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/circles/page.tsx) hardcodes `"9 PGCB GRID CIRCLES"` and uses legacy CSS classes. | Upgrade `/circles` to modern Tailwind card grid showing live circle count (`20` Branch Committees / Grid Circles) and member counts per circle. |
| **Grid Circle Detail (`/circles/[slug]`)** | Hardcoded array in [`circles/[slug]/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/circles/%5Bslug%5D/page.tsx#L2-L3) | ❌ **Broken / Hardcoded Demo Data**: Hardcodes `const allowed=['ঢাকা','চট্টগ্রাম',...]` (only 9 names, 404s on the 20 official circles) and renders fake names `প্রকৌ. উদাহরণ নাম 1/2/3`. | Replace with dynamic lookup against `GET /api/v1/public/circles` + `GET /api/v1/public/circles/{id}/committee` + circle member directory preview. |
| **Public Member Directory (`/members`)** | `GET /api/v1/public/members` | ✅ **Dynamic** with search, circle filter, and pagination. | Ensure privacy-safe public projection (no NID, personal address, or private phone exposure) and verify with 1,457-member dataset. |
| **Events (`/events`, `/events/[id]`, `/events/[id]/register`)** | `GET /api/v1/public/events`, `/api/v1/event/{id}` | 🟡 **Legacy UI Styling**: Functional API integration, but uses minified 1-line legacy CSS classes (`section`, `grid-3`, `IDEB EVENTS`) without loading/empty states. | Upgrade to modern institutional Tailwind UI with proper loading, empty state, and responsive cards. |
| **Journal (`/journal`, `/journal/[id]`)** | `GET /api/v1/public/journals` | 🟡 **Legacy UI Styling**: Functional API fetch, but uses minified 1-line legacy CSS without search/category filter or empty states. | Upgrade to modern Tailwind publication layout with category tabs, PDF viewer/download, and empty state. |
| **Media Gallery (`/media`, `/gallery`)** | `GET /api/v1/public/media` | 🟡 **Legacy UI Styling**: `/gallery` redirects to `/media`, which uses minified 1-line legacy CSS (`▧` placeholder, no actual `<img>` rendering for `x.url`). | Upgrade `/media` to render actual image thumbnails (`x.thumbnail_url || x.url`), lightbox modal, and category/event filters. |
| **Contact Page (`/contact`)** | `POST /api/v1/public/contact` | 🟡 **Legacy UI Styling**: Minified component; needs institutional contact cards driven by `public/settings` + interactive ticket confirmation. | Upgrade to modern responsive two-column layout with live Secretariat contact info and ticket reference display. |

---

## 4. Consolidated Stage 1 Findings Report

### 4.1 Confirmed Completed Features
1. **Authentication & Session Security**: Registration, email verification, login, `HttpOnly` cookie + Bearer JWT support, session listing/revocation (`/portal/security`), password change/reset, and Admin TOTP MFA (`/api/v1/admin/mfa/*`).
2. **6-Role RBAC & Circle Isolation**: Enforced server-side via [`permissions.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/permissions.py) and [`deps.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/core/deps.py) across `SUPER_ADMIN`, `CENTRAL_ADMIN`, `CIRCLE_ADMIN`, `AUDITOR`, `MEMBER`, and `APPLICANT`.
3. **End-to-End Membership Lifecycle**: Public & authenticated application submission, document upload with magic-byte validation (`PDF`, `PNG`, `JPEG`, `WEBP`), public application tracking (`/membership/track`), admin review state machine (`DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `CORRECTION_REQUIRED` / `APPROVED` / `PAYMENT_PENDING` → `ACTIVE` / `REJECTED`), and automatic `PGD-YYYY-XXXX` ID assignment.
4. **Official 1,457-Member Voter/Member Dataset (`2026–2028`)**: Extracted from the official 51-page election roll PDF into [`pgcb_members_official_2026_2028.csv`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/data/pgcb_members_official_2026_2028.csv), [`.json`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/data/pgcb_members_official_2026_2028.json), and [`.sql`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/data/pgcb_members_official_2026_2028.sql) with idempotent import script [`import_official_member_list.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/scripts/import_official_member_list.py).
5. **Payment Processing & Receipts**: Sandbox simulation, manual challan review, bKash Tokenized Checkout, Nagad & SSLCommerz integrations, HMAC webhook verification with replay deduplication (`payment_webhook_events`), and PDF receipt generation.
6. **Digital ID Cards, Certificates & Public QR Verification**: CR80 front/back PNG & PDF generation, certificate wallet, and cryptographic HMAC-SHA256 verification endpoints (`/verify`, `/member/verify/[membership_id]`, `/certificate/[token]`).
7. **Institutional AI Knowledge Engine**: Document chunking, hybrid lexical + optional OpenAI embeddings retrieval, and LLM RAG synthesis with deterministic local fallback.

### 4.2 Broken Features
1. **Circle Detail Route (`/circles/[slug]`)**: [`apps/web/app/circles/[slug]/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/circles/%5Bslug%5D/page.tsx) hardcodes an `allowed` list of 9 generic region names (`['ঢাকা','চট্টগ্রাম',...]`) and returns a `404 notFound()` for the 20 real Diprokous Grid Circles (e.g., `কেন্দ্রীয় দপ্তর, ঢাকা`, `গ্রিড সার্কেল-১, ঢাকা`, `জিএমডি, ঢাকা-নর্থ`, etc.). When it does render, it displays hardcoded placeholder names (`প্রকৌ. উদাহরণ নাম 1`, `2`, `3`) instead of querying the backend API.
2. **Media Gallery Image Rendering (`/media`)**: [`apps/web/app/media/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/media/page.tsx) renders a static `▧` text symbol inside `<div className="media-image">▧</div>` instead of rendering the actual `<img src={x.thumbnail_url || x.url} />` from `MediaAsset`.
3. **Committee Message Page (`/committee/message`)**: [`apps/web/app/committee/message/page.tsx`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/apps/web/app/committee/message/page.tsx) displays a hardcoded fictional name (`প্রকৌশলী মোঃ আব্দুর রহমান`) rather than fetching the active President/General Secretary from `/api/v1/public/committee`.

### 4.3 Missing Features
1. **Root `render.yaml` Blueprint**: Required by Phase 14 for automated Render deployment of PostgreSQL (`pgcb-portal-db`), FastAPI (`pgcb-portal-api` with persistent disk at `/var/data/uploads`), and Next.js (`pgcb-portal-web`).
2. **Unified Seed/Bootstrap Orchestrator**: While [`services/api/app/seed.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/seed.py) and [`services/api/scripts/import_official_member_list.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/scripts/import_official_member_list.py) exist separately, `seed.py` still seeds 9 generic geographic circles (`ঢাকা`, `চট্টগ্রাম`, etc.) and demo committee names (`প্রকৌ. মো. আরিফুল ইসলাম`) if run directly without the official 20-circle dataset.
3. **Language Toggle Persistence**: `Header.tsx` has a `bn`/`en` state toggle button (`language`), but it is local to `Header` state and does not propagate or switch labels globally.

### 4.4 Duplicate Implementations
1. **Frontend Route Aliases / Duplicates**:
   - `/committee` (legacy CSS) vs. `/leadership` (modern Tailwind Central + Circle Committee page).
   - `/member` vs. `/portal` (`/member` re-exports `/portal`).
   - `/gallery` vs. `/media` (`/gallery` redirects to `/media`).
   - `/admin/applications`, `/admin/membership-applications`, and `/admin/memberships/applications` (3 routes pointing to the same component).
   - `/admin/gallery` and `/admin/media` (2 routes pointing to the same component).
   - `/admin/permissions` and `/admin/roles` (2 routes pointing to the same component).
2. **Database Schema Overlap (`core.py` vs. `v14` & `payments.py`)**:
   - `circles` (active FK target for `members`, `committee_members`, `membership_applications`) vs. `grid_circles` (standalone table from `v14`).
   - `payment_transactions` (primary table) vs. `payments` (secondary table synced in `payments.py`) vs. `gateway_payment_transactions` (`models/payments.py`).
   - `payment_webhook_events` vs. `payment_webhooks`.
   - `news_articles` (`News`) vs. `news` (`NewsEntry`).
   - `audit_logs` (`AuditLog`) vs. `security_audit_logs` (`SecurityAuditLog`).
3. **Duplicate OpenAPI Operation IDs**:
   - `/api/v1/member/card.pdf` and `/api/v1/member/card/pdf` share function `digital_card_pdf`.
   - `/api/v1/member/payments/{payment_id}/receipt.pdf` and `/api/v1/member/payments/{payment_id}/receipt/pdf` share function `download_payment_receipt_pdf`.

### 4.5 Technical Debt
1. **Legacy Minified Single-Line TSX Files**: 14 files in `apps/web/app/` (`circles/page.tsx`, `circles/[slug]/page.tsx`, `committee/page.tsx`, `events/page.tsx`, `events/[id]/page.tsx`, `events/[id]/register/page.tsx`, `events/ticket/[token]/page.tsx`, `journal/page.tsx`, `journal/[id]/page.tsx`, `media/page.tsx`, `contact/page.tsx`, `privacy/page.tsx`, `terms/page.tsx`, `accessibility/page.tsx`) are formatted as 1–6 line minified files using legacy CSS classes instead of the modern Tailwind design system used across the rest of the portal.
2. **Python `datetime.utcnow()` Deprecation Warnings**: 249 warnings emitted during `pytest` runs on Python 3.13 due to `datetime.utcnow()` calls across SQLAlchemy column defaults and service modules.
3. **`seed.py` Demo Data**: [`services/api/app/seed.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/seed.py) contains demo committee members (`প্রকৌ. মো. আরিফুল ইসলাম`, `প্রকৌ. তানভীর আহমেদ`, `প্রকৌ. নুসরাত জাহান`) and sample notices that should be replaced with clean, non-fictional institutional bootstrap defaults + the 20 official Diprokous circles.

### 4.6 Deployment Blockers
1. **Missing `render.yaml`**: Needed for turnkey Render deployment.
2. **Hardcoded Demo Content on `/circles/[slug]`, `/committee/message`, and `seed.py`**: Must be cleaned before production launch so no placeholder names (`প্রকৌ. উদাহরণ নাম 1`, `প্রকৌশলী মোঃ আব্দুর রহমান`, `প্রকৌ. মো. আরিফুল ইসলাম`) ever appear on the live institutional portal.
3. **Legacy Public Pages Visual Parity**: `/events`, `/journal`, `/media`, `/circles`, `/committee`, and `/contact` must be brought into visual parity with the modern institutional Tailwind design system (`#0F172A` Navy, `#0F766E` Grid Teal, `#D97706` Amber Accent, Hind Siliguri / Noto Sans Bengali typography).
