# v0.7 Transactions, Automation & Publishing

## Payment flow

1. Member creates a payment intent.
2. Provider adapter returns a provider transaction reference.
3. Provider calls `/api/v1/payments/webhooks/{provider}`.
4. Request body is validated with HMAC-SHA256 using the configured webhook secret.
5. `event_id` is stored in `payment_webhook_events` so retries are idempotent.
6. A successful membership payment creates a `membership_renewals` record and extends membership by 365 days.
7. A successful event payment marks the registration paid.

The repository intentionally stops at the adapter boundary for bKash/Nagad/SSLCommerz; live credentials and provider-specific API contracts must be supplied for the selected merchant accounts.

## Notification worker

`python -m app.worker` processes queued email/SMS deliveries and runs membership lifecycle checks. Failed deliveries receive retry scheduling and are capped at five attempts.

## Membership lifecycle

Active memberships receive reminders 30, 7 and 1 day before expiry. Expired active memberships are marked `EXPIRED`. Reminder records are unique per member, validity date and reminder type.

## Event certificates

Administrators can generate a certificate only after check-in. PNG and PDF files are generated into the configured storage backend; a SHA-256-hashed verification token supports public verification.

## CMS workflow

Content entities supported in v0.7: `CIRCULAR`, `JOURNAL`, `EVENT`. Each can transition through the workflow endpoint. `SCHEDULED` items are automatically published by the worker when their scheduled timestamp is reached.
