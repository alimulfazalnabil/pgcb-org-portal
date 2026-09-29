# PGCB Organization Portal — Phase 3.2 Backend API Endpoint Audit (`docs/API_AUDIT.md`)

- **Repository**: `alimulfazalnabil/pgcb-org-portal`
- **FastAPI Entry Point**: [`services/api/app/main.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/main.py)
- **Total Registered OpenAPI Paths**: `212` (`247` HTTP operations across `16` router modules + root observability routes)
- **Audit Date**: September 29, 2026

---

## 1. Root & Observability Endpoints ([`app/main.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/main.py))

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET, HEAD` | `/` | No | Public | None | Service metadata (`service`, `status`, `version`, `/docs`, `/health`, `/ready`, `/live`) | None | `200` |
| `GET` | `/health`, `/api/v1/health` | No | Public | None | `{status: "ok", database: "connected", service: "pgcb-api", version: "1.0.0-rc1"}` | None | `200` |
| `GET` | `/live` | No | Public | None | `{status: "alive", service: "pgcb-api", version: "1.0.0-rc1"}` | None | `200` |
| `GET` | `/ready` | No | Public | None | `{status: "ready", database: "ok"}` | `SELECT 1` probe | `200, 503` |
| `GET` | `/metrics` | Optional Bearer (`METRICS_TOKEN` in prod) | System / Prometheus | `Authorization: Bearer <token>` | Prometheus text exposition format | In-memory metrics registry | `200, 401, 404` |

---

## 2. Authentication & Session Security ([`app/routers/auth.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/auth.py))

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | No | Public | `RegisterIn` (`name_bn`, `name_en`, `email`, `phone`, `password`, `circle_id`, `designation_bn`, `employee_id`) | `AuthOut` (`access_token`, `user`, `verification_token_preview` in dev/test) | `users`, `members`, `email_verification_tokens`, `user_sessions`, `audit_logs` | `200, 400, 409, 422, 429` |
| `POST` | `/api/v1/auth/login` | No | Public | `LoginIn` (`email`, `password`, optional `mfa_code`) | `AuthOut` + sets `HttpOnly` cookie `pgcb_access_token` | `users`, `members`, `user_sessions`, `audit_logs` | `200, 401, 403, 422, 429` |
| `POST` | `/api/v1/auth/logout` | Yes | Any Authenticated | Cookie / Bearer token | `{status: "logged_out"}` + clears cookie | `user_sessions`, `audit_logs` | `200, 401` |
| `POST` | `/api/v1/auth/logout-all` | Yes | Any Authenticated | None | `{status: "logged_out_all", revoked_sessions: int}` | `user_sessions`, `audit_logs` | `200, 401` |
| `GET` | `/api/v1/auth/me` | Yes | Any Authenticated | None | `UserOut` (`id`, `email`, `name_bn`, `role`, `permissions`, `membership_id`, `membership_status`, `circle_id`) | `users`, `members`, `circles` | `200, 401` |
| `POST` | `/api/v1/auth/verify-email` | No | Public | `TokenConfirmIn` (`token`) | `{status: "verified"}` | `email_verification_tokens`, `users`, `audit_logs` | `200, 400, 422` |
| `POST` | `/api/v1/auth/resend-verification` | No | Public | `EmailRequestIn` (`email`) | `{status: "sent"}` | `email_verification_tokens`, `users`, `notification_deliveries` | `200, 429` |
| `POST` | `/api/v1/auth/password-reset/request` | No | Public | `PasswordResetRequestIn` (`email`) | `{status: "sent"}` | `password_reset_tokens`, `users`, `notification_deliveries` | `200, 429` |
| `POST` | `/api/v1/auth/password-reset/confirm` | No | Public | `PasswordResetConfirmIn` (`token`, `new_password`) | `{status: "password_updated"}` | `password_reset_tokens`, `users`, `user_sessions`, `audit_logs` | `200, 400, 422` |
| `POST` | `/api/v1/auth/password/change` | Yes | Any Authenticated | `PasswordChangeIn` (`current_password`, `new_password`) | `{status: "password_changed"}` | `users`, `user_sessions`, `audit_logs` | `200, 400, 401` |
| `GET` | `/api/v1/auth/sessions` | Yes | Any Authenticated | None | `list[SessionOut]` (`id`, `created_at`, `expires_at`, `last_seen_at`, `is_current`) | `user_sessions` | `200, 401` |
| `DELETE, POST` | `/api/v1/auth/sessions/{session_id}` (`/revoke`) | Yes | Owner of Session | Path `session_id` | `{status: "revoked"}` | `user_sessions`, `audit_logs` | `200, 401, 404` |

---

## 3. Public Institutional & Verification Endpoints ([`app/routers/public.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/public.py))

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/public/stats` | No | Public | None | `{active_members, active_circles, publications, documents_count, upcoming_events}` | `members`, `circles`, `journals`, `documents`, `events` | `200` |
| `GET` | `/api/v1/public/settings` | No | Public | None | `dict[str, str]` (public site settings) | `site_settings` | `200` |
| `GET` | `/api/v1/public/circles` | No | Public | None | `list[CircleOut]` (`id`, `name_bn`, `name_en`, `description_bn`, `member_count`) | `circles`, `members` | `200` |
| `GET` | `/api/v1/public/circles/{circle_id}` | No | Public | Path `circle_id` | `CircleDetailOut` | `circles`, `members`, `committee_members` | `200, 404` |
| `GET` | `/api/v1/public/circles/{circle_id}/committee` | No | Public | Path `circle_id` | `list[CommitteeOut]` | `committee_members` | `200` |
| `GET` | `/api/v1/public/committee` | No | Public | Query `circle_id` (optional) | `list[CommitteeOut]` | `committee_members` | `200` |
| `GET` | `/api/v1/public/members` | No | Public | Query `q`, `circle_id`, `designation`, `page`, `limit` | Paginated privacy-safe member directory (`items`, `total`, `page`, `pages`) | `members`, `users`, `circles` | `200` |
| `POST` | `/api/v1/public/membership/apply` | No | Public | `PublicMembershipApplyIn` | `{application_no, member_id, status, tracking_url}` | `users`, `members`, `membership_applications`, `audit_logs` | `200, 201, 400, 409, 422` |
| `GET` | `/api/v1/public/membership/track/{application_no}` | No | Public | Path `application_no` | Application status, timeline & circle info | `members`, `membership_applications`, `application_reviews` | `200, 404` |
| `GET` | `/api/v1/public/verify/{membership_id}` & `/verify-member/{membership_id}` | No | Public | Path `membership_id` | `VerificationOut` (`verified`, `name_bn`, `name_en`, `membership_id`, `employee_id`, `designation_bn`, `circle_bn`, `status`, `validity_date`) | `members`, `users`, `circles` | `200, 404` |
| `GET` | `/api/v1/public/verify-token/{token}` | No | Public | Path `token` (HMAC-SHA256 signed QR token) | `VerificationOut` | `members`, `users`, `circles` | `200, 400, 404` |
| `GET` | `/api/v1/public/circulars`, `/circulars/{circular_id}` | No | Public | Query `category`, `q`, `limit` | `list[CircularOut]` / `CircularOut` | `circulars` | `200, 404` |
| `GET` | `/api/v1/public/journals`, `/journals/{journal_id}` | No | Public | Query `category`, `limit` | `list[JournalOut]` / `JournalOut` | `journals` | `200, 404` |
| `GET` | `/api/v1/public/events` | No | Public | Query `upcoming_only`, `limit` | `list[EventOut]` | `events` | `200` |
| `GET` | `/api/v1/public/media` | No | Public | Query `media_type`, `event_id` | `list[MediaOut]` | `media_assets` | `200` |
| `GET` | `/api/v1/public/notices` | No | Public | Query `category`, `limit` | `list[NoticeOut]` | `notices` | `200` |
| `POST` | `/api/v1/public/contact` | No | Public | `ContactIn` (`name`, `email`, `phone`, `subject`, `message`) | `{status: "submitted", ticket_no: str}` | `contact_messages`, `contact_inquiry_meta` | `200, 422, 429` |
| `GET` | `/api/v1/public/search`, `/search/suggestions` | No | Public | Query `q`, `type`, `limit` | Federated search results across notices, circulars, documents, events, journals, members | `notices`, `circulars`, `documents`, `events`, `journals`, `members` | `200` |
| `GET` | `/api/v1/public/assets/{filename}` | No | Public | Path `filename` | Streamed public image/file | Local/persistent storage (`public/`) | `200, 404` |

---

## 4. Member Self-Service & Digital ID Endpoints ([`app/routers/membership.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/membership.py) & [`app/routers/card.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/card.py))

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/member/dashboard` | Yes | `MEMBER` / `APPLICANT` | None | `MemberDashboardOut` (greeting, membership status card, days remaining, counts) | `members`, `users`, `circles`, `certificates`, `notifications` | `200, 401` |
| `GET, PUT, PATCH` | `/api/v1/member/profile` | Yes | `MEMBER` / `APPLICANT` | `MemberProfileIn` | `MemberProfileOut` | `members`, `users`, `circles`, `audit_logs` | `200, 400, 401, 422` |
| `GET` | `/api/v1/member/application` | Yes | `MEMBER` / `APPLICANT` | None | Application status, review notes, documents count | `members`, `membership_applications`, `application_reviews` | `200, 401` |
| `POST` | `/api/v1/member/application/draft` | Yes | `MEMBER` / `APPLICANT` | `ApplicationDraftIn` | Updated draft state | `members`, `membership_applications` | `200, 400, 401` |
| `POST` | `/api/v1/member/application`, `/api/v1/member/apply` | Yes | `MEMBER` / `APPLICANT` | Optional `ApplicationSubmitIn` | Submitted application (`SUBMITTED`) | `members`, `membership_applications`, `application_reviews`, `notifications`, `audit_logs` | `200, 400, 401` |
| `POST` | `/api/v1/member/application/cancel` | Yes | `MEMBER` / `APPLICANT` | Optional reason | Cancelled application (`CANCELLED`) | `members`, `membership_applications`, `application_reviews` | `200, 400, 401` |
| `GET` | `/api/v1/member/documents` | Yes | Owner Member | None | `list[MemberDocumentOut]` | `member_documents` | `200, 401` |
| `POST` | `/api/v1/member/documents` | Yes | Owner Member | `multipart/form-data` (`document_type`, `file`) | `MemberDocumentOut` | `member_documents`, `audit_logs` + `private/` storage | `200, 400, 401, 413, 415` |
| `GET` | `/api/v1/member/documents/{document_id}/download` | Yes | Owner Member or Admin (`BOLA` enforced) | Path `document_id` | Binary file stream (`PDF`/`PNG`/`JPEG`) | `member_documents` + `private/` storage | `200, 401, 403, 404` |
| `GET` | `/api/v1/member/renewal-options`, `/renewals` | Yes | `MEMBER` | None | Renewal plans (`1YR`, `2YR`, `LIFE`) / renewal history | `membership_renewals`, `site_settings` | `200, 401` |
| `POST` | `/api/v1/member/renewal/initiate` | Yes | `MEMBER` | `RenewalInitiateIn` (`plan_code`, `provider`) | Created payment transaction & renewal record | `payment_transactions`, `membership_renewals` | `200, 400, 401` |
| `GET` | `/api/v1/member/certificates` | Yes | `MEMBER` | None | `list[CertificateWalletItem]` | `certificates` | `200, 401` |
| `GET, POST` | `/api/v1/member/notifications`, `/unread-count`, `/{id}/read`, `/read-all` | Yes | Owner User | None / `notification_id` | In-app notifications & unread badge count | `notifications` | `200, 401, 404` |
| `GET, PUT` | `/api/v1/member/notification-preferences` | Yes | Owner User | `NotificationPreferences` | Updated preferences | `site_settings` | `200, 401` |
| `GET` | `/api/v1/member/card`, `/card/back` | Yes | Active `MEMBER` or Admin | None | High-res PNG image stream (`image/png`) | `members`, `users`, `circles` | `200, 401, 403` |
| `GET` | `/api/v1/member/card/pdf`, `/card.pdf` | Yes | Active `MEMBER` or Admin | None | Print-ready CR80 PDF stream (`application/pdf`) | `members`, `users`, `circles` | `200, 401, 403` |
| `GET` | `/api/v1/member/card/details`, `/card/metadata` | Yes | Active `MEMBER` or Admin | None | Card metadata + signed QR verification URL | `members`, `users`, `circles` | `200, 401, 403` |
| `GET` | `/api/v1/member/cards/{member_id}/png`, `/pdf` | Yes | Admin (`member.read`) | Path `member_id` | PNG / PDF stream for specified member | `members`, `users`, `circles` | `200, 401, 403, 404` |

---

## 5. Payments, Sandbox & Webhook Endpoints ([`app/routers/payments.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/payments.py) & [`app/routers/payment_webhooks.py`](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/services/api/app/routers/payment_webhooks.py))

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/public/membership-fees`, `/api/v1/member/membership-fee` | No / Yes | Public / Member | Query `membership_type` | Fee breakdown (`GENERAL`, `LIFE`, `RENEWAL`) | `site_settings` | `200` |
| `GET` | `/api/v1/member/payments` | Yes | Owner Member | None | `list[PaymentOut]` | `payment_transactions`, `payments` | `200, 401` |
| `POST` | `/api/v1/member/payments`, `/checkout`, `/initiate`, `/api/v1/payments/checkout` | Yes | Authenticated User | `PaymentCreateIn` (`purpose`, `amount`, `provider`, `membership_plan_id`, `idempotency_key`) | `PaymentCheckoutOut` (`transaction_ref`, `checkout_url`, `status`, `amount`) | `payment_transactions`, `payments`, `audit_logs` | `200, 201, 400, 401, 409` |
| `POST` | `/api/v1/member/payments/{payment_id}/confirm` | Yes | Owner / Admin | Confirmation payload | Updated payment status | `payment_transactions`, `payments`, `members`, `memberships` | `200, 400, 401, 404` |
| `POST` | `/api/v1/payments/sandbox/simulate` | Yes (or Sandbox key) | Authenticated / Sandbox | `SandboxSimulateIn` (`transaction_ref`, `status`, `provider`) | Simulated webhook execution & membership activation | `payment_transactions`, `payments`, `payment_webhook_events`, `members`, `memberships`, `certificates`, `audit_logs` | `200, 400, 403, 404` |
| `POST` | `/api/v1/payments/webhook/{provider}`, `/webhooks/{provider}`, `/api/v1/webhook/{provider}`, `/callback/{provider}` | HMAC Signature (`X-Payment-Signature`) | Gateway Webhook | Raw JSON payload + signature header | `{status: "processed", idempotent: bool}` | `payment_webhook_events`, `payment_transactions`, `payments`, `members`, `memberships`, `certificates`, `audit_logs` | `200, 400, 401, 404` |
| `GET` | `/api/v1/member/payments/{payment_id}/receipt`, `/receipt/pdf`, `/receipt.pdf` | Yes | Owner Member or Finance Admin (`BOLA` enforced) | Path `payment_id` | JSON receipt metadata / signed PDF receipt stream | `payment_transactions`, `members`, `users` | `200, 401, 403, 404` |
| `GET` | `/api/v1/public/receipts/verify/{token_or_receipt_no}` | No | Public | Path `token_or_receipt_no` | Cryptographic receipt authenticity verification | `payment_transactions`, `payments`, `members` | `200, 404` |

---

## 6. Notices, Documents, Certificates, Events & CMS Endpoints (`notices.py`, `documents.py`, `certificates.py`, `event_registration.py`, `events_public.py`, `cms.py`, `workflows.py`)

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/notices`, `/notices/urgent`, `/notices/{notice_id}` | No | Public | Query `category`, `priority`, `q`, `page`, `limit` | `list[NoticeOut]` / `NoticeOut` | `notices` | `200, 404` |
| `POST, PUT, DELETE` | `/api/v1/notices`, `/notices/{notice_id}` | Yes | Admin (`notice.write`) | `NoticeCreateIn` / `NoticeUpdateIn` | `NoticeOut` / `{status: "deleted"}` | `notices`, `content_revisions`, `audit_logs` | `200, 201, 401, 403, 404` |
| `GET` | `/api/v1/documents`, `/documents/{document_id}` | No | Public | Query `category`, `page`, `limit` | `list[DocumentOut]` / `DocumentOut` | `documents` | `200, 404` |
| `GET` | `/api/v1/documents/{document_id}/download`, `/signed-url` | No (if published) / Yes | Public / Member | Path `document_id` | File stream + increments `download_count` / signed URL | `documents` + storage | `200, 403, 404` |
| `POST, PUT, DELETE` | `/api/v1/documents`, `/documents/upload`, `/documents/{document_id}` | Yes | Admin (`document.write`) | `DocumentCreateIn` or `multipart/form-data` | `DocumentOut` | `documents`, `audit_logs` + storage | `200, 201, 400, 401, 403` |
| `GET` | `/api/v1/certificates/me` | Yes | Authenticated User | None | `list[CertificateOut]` | `certificates` | `200, 401` |
| `GET` | `/api/v1/certificates/verify/{token}` | No | Public | Path `token` or `certificate_no` | Verified certificate details | `certificates`, `members`, `event_registrations` | `200, 404` |
| `GET` | `/api/v1/certificates/{certificate_no}/download` (`.pdf`), `/preview` (`.png`) | No (signed token) / Yes | Owner / Public with token | Path `certificate_no` | PDF / PNG stream | `certificates` + storage | `200, 404` |
| `POST` | `/api/v1/certificates/event-registrations/{registration_id}` | Yes | Admin (`certificate.write`) | Path `registration_id` | Issued event certificate | `certificates`, `event_registrations`, `audit_logs` | `200, 201, 401, 403, 404` |
| `GET` | `/api/v1/event/{event_id}` | No | Public | Path `event_id` | `EventDetailOut` | `events`, `event_registrations` | `200, 404` |
| `POST` | `/api/v1/events/{event_id}/registrations`, `/registrations/member` | No / Yes | Public / Member | `EventRegistrationIn` | Issued ticket (`ticket_code`, `qr_token`) | `event_registrations`, `events`, `payment_transactions` | `200, 201, 400, 409` |
| `GET` | `/api/v1/events/registrations/me`, `/{ticket_token}`, `/{ticket_token}/qr` | Yes / No | Member / Public token | Path `ticket_token` | Registration list / ticket status / QR PNG | `event_registrations`, `events` | `200, 401, 404` |
| `GET` | `/api/v1/public/news`, `/news/{slug_or_id}`, `/public/announcements`, `/homepage-config`, `/rss.xml`, `/sitemap.xml`, `/robots.txt` | No | Public | Query filters | News articles, banners, RSS XML, Sitemap XML | `news_articles`, `news`, `announcements`, `site_settings` | `200, 404` |
| `GET, POST, PUT, DELETE` | `/api/v1/admin/news`, `/admin/announcements`, `/admin/seo/{entity_type}/{entity_id}`, `/admin/revisions/{entity_type}/{entity_id}`, `/admin/workflows` | Yes | Admin (`content.write`) | CMS payloads | Updated CMS entities, revisions & workflow transitions | `news_articles`, `announcements`, `seo_metadata`, `content_revisions`, `content_workflows`, `audit_logs` | `200, 201, 401, 403, 404` |

---

## 7. Admin, Secretariat, Helpdesk & AI Intelligence Endpoints (`admin.py`, `secretariat.py`, `helpdesk.py`, `ai.py`)

| METHOD | PATH | AUTH | ROLE | REQUEST | RESPONSE | DATABASE | STATUS CODES |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/stats`, `/circle-dashboard`, `/circles/{id}/dashboard`, `/analytics/executive`, `/data-quality` | Yes | Admin (`admin.stats` / Circle-scoped for `CIRCLE_ADMIN`) | Optional filters | Dashboard KPIs, circle breakdown & data quality metrics | `members`, `circles`, `payment_transactions`, `events`, `notices` | `200, 401, 403` |
| `GET` | `/api/v1/admin/memberships/applications`, `/applications/{member_id}` | Yes | Admin (`member.review` / Circle-scoped for `CIRCLE_ADMIN`) | Query `status`, `circle_id`, `q`, `limit` | Application list with status KPI counts / detailed application dossier | `members`, `users`, `circles`, `membership_applications`, `application_reviews`, `member_documents`, `payment_transactions` | `200, 401, 403, 404` |
| `POST` | `/api/v1/admin/memberships/applications/{member_id}/action` | Yes | Admin (`member.review`) | `ApplicationActionIn` (`action`, `note`, `circle_id`) | Transitioned application state (`UNDER_REVIEW`, `CORRECTION_REQUIRED`, `APPROVE`, `PAYMENT_PENDING`, `ACTIVATE`, `REJECT`) + audit log + notification | `members`, `membership_applications`, `application_reviews`, `memberships`, `certificates`, `notifications`, `audit_logs` | `200, 400, 401, 403, 404` |
| `GET, POST` | `/api/v1/admin/members`, `/members/{member_id}`, `/members/{member_id}/review` | Yes | Admin (`member.read` / `member.review`) | Query filters / `MemberReviewIn` | Member list / detail / updated status | `members`, `users`, `circles`, `memberships`, `audit_logs` | `200, 401, 403, 404` |
| `POST` | `/api/v1/admin/imports/members/preview`, `/commit` | Yes | Admin (`SUPER_ADMIN` / `CENTRAL_ADMIN`) | CSV file upload (`multipart/form-data`) | Dry-run validation preview / bulk upsert summary (`created`, `updated`, `circles_created`) | `circles`, `grid_circles`, `users`, `members`, `memberships`, `membership_applications`, `audit_logs` | `200, 400, 401, 403` |
| `GET` | `/api/v1/admin/exports/members.csv`, `.xlsx`, `.pdf`, `/applications.csv`, `/payments.csv`, `/event-registrations.csv`, `/certificates.csv`, `/audit.csv` | Yes | Admin (`admin.stats` / `AUDITOR`) | Query filters | Downloadable CSV / XLSX / PDF streams | Respective domain tables + `audit_logs` | `200, 401, 403` |
| `GET, POST` | `/api/v1/admin/documents/{document_id}/download`, `/review` | Yes | Admin (`member.review`) | Path `document_id` / `DocumentReviewIn` | Private member document stream / updated `review_status` | `member_documents`, `audit_logs` | `200, 401, 403, 404` |
| `GET, PATCH` | `/api/v1/admin/payments`, `/payments/{payment_id}` | Yes | Admin (`finance.read` / `finance.verify`) | Query filters / `PaymentAdminUpdateIn` | Financial ledger / verified payment + membership activation | `payment_transactions`, `payments`, `members`, `memberships`, `certificates`, `audit_logs` | `200, 400, 401, 403, 404` |
| `GET, POST, PUT, DELETE` | `/api/v1/admin/circles`, `/committee`, `/circulars`, `/journals`, `/events`, `/media`, `/users`, `/roles`, `/permissions`, `/settings`, `/email-templates` | Yes | Admin (permission-gated) | Respective CRUD schemas | Created/updated/deleted institutional records | Respective tables + `audit_logs` | `200, 201, 400, 401, 403, 404` |
| `GET` | `/api/v1/admin/audit`, `/audit-logs`, `/reports/overview`, `/reports/mis`, `/reports/financial`, `/health`, `/system/health` | Yes | Admin (`audit.read` / `admin.stats`) | Query filters | Audit logs, MIS/financial reports, and deep system health telemetry | `audit_logs`, `security_audit_logs`, `members`, `payment_transactions` | `200, 401, 403` |
| `GET, POST` | `/api/v1/admin/mfa/status`, `/setup`, `/enable`, `/disable`, `/backup-codes` | Yes | Admin user | TOTP code verification | MFA provisioning URI, backup codes & status | `users`, `audit_logs` | `200, 400, 401` |
| `GET, POST` | `/api/v1/public/helpdesk/topics`, `/helpdesk/ask`, `/api/v1/ai/ask`, `/api/v1/ai/chat`, `/api/v1/knowledge/search` | No / Yes | Public / Member / Admin | Question / search query | Grounded Bengali/English answer with citations (`KnowledgeDocument` + optional OpenAI `gpt-4o-mini` synthesis) | `knowledge_documents`, `knowledge_chunks`, `knowledge_faqs`, `ai_query_logs` | `200, 422, 429` |
| `GET, POST, PATCH` | `/api/v1/admin/knowledge/documents`, `/ingest-file`, `/admin/ai/faqs`, `/generate-faqs`, `/content-assist`, `/analytics` | Yes | Admin (`SUPER_ADMIN` / `CENTRAL_ADMIN`) | Knowledge ingestion / FAQ curation payloads | Chunked & embedded knowledge documents, smart FAQs, and AI usage analytics | `knowledge_documents`, `knowledge_chunks`, `knowledge_faqs`, `ai_query_logs` | `200, 201, 401, 403` |
