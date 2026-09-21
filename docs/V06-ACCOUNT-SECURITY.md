# v0.6 — Account Security & Operations

## Added

- Email verification token lifecycle with one-time, expiring tokens.
- Configurable `REQUIRE_EMAIL_VERIFICATION` gate for login.
- Verification resend endpoint with non-enumerating response.
- Member-facing verification and resend pages.
- Redis-backed rate limiting with automatic in-memory fallback when Redis is unavailable.
- Member/admin session revocation UI and API (from v0.5).
- CSV export endpoints for members, event registrations and payments.

## Email verification flow

1. User creates account.
2. API stores a hashed verification token with an expiry.
3. API attempts transactional email delivery.
4. In development the token is returned to facilitate local testing; production never returns it.
5. User opens `/verify-email?token=...`.
6. API marks `users.email_verified=true` and invalidates the token.

Set `REQUIRE_EMAIL_VERIFICATION=true` after SMTP delivery is configured and tested.

## Rate limiting

The API prefers Redis for shared counters across multiple instances. If Redis is unavailable, it falls back to an in-memory limiter so development remains functional. For production, Redis should be highly available and complemented by an edge/WAF control.

## CSV exports

Admin users with the corresponding permissions can download:

- `/api/v1/admin/exports/members.csv`
- `/api/v1/admin/exports/event-registrations.csv`
- `/api/v1/admin/exports/payments.csv`

Exports are generated from the live database and are not persisted as files on the server.

## Production checklist

- Generate a strong JWT secret.
- Supply a valid Fernet key in `MFA_ENCRYPTION_KEY`.
- Configure SMTP and verify deliverability.
- Set `REQUIRE_EMAIL_VERIFICATION=true`.
- Run Alembic migrations.
- Use Redis for distributed rate limiting.
- Keep Blob containers private and use signed URLs.
- Put the API behind a WAF/edge service and TLS.
