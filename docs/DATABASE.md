# PGCB Organization Portal — Database Schema & Migrations

## 1. Database Engine & ORM

- **ORM**: SQLAlchemy 2.0 (`services/api/app/models/core.py`)
- **Migrations**: Alembic (`services/api/alembic/versions/`)
- **Production Database**: PostgreSQL 16 (`pgcb-org-db` on Render)
- **Local Development / CI Test Database**: SQLite 3 (`portal.db` / `test_portal.db`)

---

## 2. Core Entities & Relationships

| Table Name | Model Class | Primary Key | Key Columns & Relationships |
| :--- | :--- | :--- | :--- |
| `users` | `User` | `id` | `email` (unique), `password_hash`, `name_bn`, `name_en`, `phone`, `role`, `is_active`, `mfa_enabled`, `mfa_secret_enc` |
| `members` | `Member` | `id` | `user_id` (FK $\rightarrow$ `users.id`), `membership_id` (unique, e.g. `PGD-2026-1001`), `employee_id`, `designation_bn`, `circle_id` (FK $\rightarrow$ `circles.id`), `status` (`PENDING`, `SUBMITTED`, `UNDER_REVIEW`, `ACTIVE`, `REJECTED`, `SUSPENDED`, `EXPIRED`), `issue_date`, `validity_date` |
| `member_documents` | `MemberDocument` | `id` | `member_id` (FK $\rightarrow$ `members.id`), `document_type`, `filename`, `storage_path`, `review_status` |
| `circles` | `Circle` | `id` | `name_bn` (unique), `name_en`, `region_bn`, `office_address_bn`, `contact_phone`, `active` |
| `committee_members` | `CommitteeMember` | `id` | `circle_id` (FK $\rightarrow$ `circles.id`), `name_bn`, `role_bn`, `session_year`, `display_order`, `active` |
| `circulars` | `Circular` | `id` | `slug` (unique), `title_bn`, `category_bn`, `priority`, `body_bn`, `attachment_url`, `visibility`, `is_published`, `published_at` |
| `notices` | `Notice` | `id` | `slug` (unique), `title_bn`, `category`, `summary_bn`, `content_bn`, `is_featured`, `is_published`, `visibility`, `published_at` |
| `organizational_documents` | `OrganizationalDocument` | `id` | `slug` (unique), `title_bn`, `category`, `file_url`, `version`, `visibility`, `is_published` |
| `events` | `Event` | `id` | `slug` (unique), `title_bn`, `event_date`, `location_bn`, `capacity`, `registration_fee`, `registration_open`, `is_published` |
| `event_registrations` | `EventRegistration` | `id` | `event_id` (FK $\rightarrow$ `events.id`), `user_id` (FK $\rightarrow$ `users.id`), `ticket_code` (unique), `registration_status`, `attendance_status`, `payment_status`, `registered_at`, `checked_in_at` |
| `payment_transactions` | `PaymentTransaction` | `id` | `user_id`, `member_id`, `event_registration_id`, `purpose` (`MEMBERSHIP` / `EVENT`), `amount`, `currency`, `provider`, `transaction_ref`, `status` (`PENDING`, `PAID`, `FAILED`, `REFUNDED`) |
| `membership_renewals` | `MembershipRenewal` | `id` | `member_id` (FK $\rightarrow$ `members.id`), `payment_id` (FK $\rightarrow$ `payment_transactions.id`), `previous_validity_date`, `new_validity_date`, `amount` |
| `certificates` | `Certificate` | `id` | `certificate_no` (unique), `verification_token_hash` (unique), `recipient_name`, `title_bn`, `issue_date`, `storage_path`, `pdf_path`, `member_id`, `event_registration_id` |
| `journals` | `Journal` | `id` | `slug` (unique), `title_bn`, `authors_bn`, `abstract_bn`, `volume`, `issue`, `pdf_url`, `is_published` |
| `media_assets` | `MediaAsset` | `id` | `title_bn`, `category_bn`, `asset_type`, `url`, `thumbnail_url`, `published` |
| `content_workflows` | `ContentWorkflow` | `id` | `entity_type`, `entity_id`, `state` (`DRAFT`, `REVIEW`, `APPROVED`, `PUBLISHED`, `ARCHIVED`), `submitted_by`, `reviewed_by`, `approved_by` |
| `audit_logs` | `AuditLog` | `id` | `user_id` (FK $\rightarrow$ `users.id`), `action`, `entity`, `entity_id`, `ip_address`, `created_at` |
| `notifications` | `Notification` | `id` | `user_id` (FK $\rightarrow$ `users.id`), `title_bn`, `body_bn`, `notification_type`, `is_read` |
| `site_settings` | `SiteSetting` | `id` | `key` (unique), `value`, `category`, `updated_at` |

---

## 3. Running Migrations

From `services/api`:

```bash
# Apply all migrations up to head
alembic upgrade head

# Check current migration revision
alembic current
```
