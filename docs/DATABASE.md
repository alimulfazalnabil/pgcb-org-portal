# Database Blueprint — v0.7

## Core entities

- `users` — accounts, role, MFA state and email verification state
- `members` — membership profile and approval state
- `circles` — regional organizational units
- `committee_members` — central/regional leadership entries
- `circulars` — official notices and circular documents
- `journals` — technical publications
- `events` — event metadata, capacity, deadlines and fees
- `event_registrations` — attendee/ticket/attendance/payment state
- `payment_transactions` — finance ledger entries and provider metadata
- `notifications` — in-app notifications
- `notification_deliveries` — per-channel delivery logs
- `member_documents` — private member files and review state
- `user_sessions` — revocable authentication sessions
- `password_reset_tokens` — one-time password reset tokens
- `email_verification_tokens` — one-time email verification tokens
- `audit_logs` — privileged action trail
- `media_assets` — public media and event media references
- `contact_messages` — secretariat inbox
- `site_settings` — runtime CMS settings

## Security-sensitive data

NID and similar identity fields are kept out of public verification responses. Member documents are stored through a private storage path and exposed only through authenticated/authorized routes. Administrator MFA secrets are stored encrypted in `users.mfa_secret_enc`.

## Indexing

Primary lookup fields such as email, membership ID, user role, member status, circle ID, publication date, event date, ticket code, payment status, notification timestamp and audit entity/action are indexed.

The Alembic chain through `f91a2c7d4e10` creates the v0.7 transaction, lifecycle, certificate and CMS workflow changes.


## v0.7 tables

- `payment_webhook_events` — signed callback audit/idempotency ledger.
- `membership_renewals` — membership renewal history.
- `membership_reminders` — unique reminder state per validity period.
- `certificates` — generated event certificates and hashed verification tokens.
- `content_workflows` — editorial state and scheduled publication metadata.

`notification_deliveries` now also stores attempt/retry scheduling and an idempotency key.
