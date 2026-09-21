# Release Notes — v0.7

## Transaction, workflow and automation layer

v0.7 extends the institutional portal from account/security operations into transaction processing, scheduled publishing, notification delivery and event certification.

### Payments
- Provider adapter boundary for `MANUAL`, `TEST`, `BKASH`, `NAGAD` and `SSLCOMMERZ`.
- Checkout intent creation with persisted transaction references.
- HMAC-SHA256 webhook verification.
- Webhook event-id idempotency ledger.
- Payment status reconciliation for membership and event registration records.

### Membership lifecycle
- Renewal history ledger.
- Automatic 30/7/1-day expiry reminders.
- Automatic `EXPIRED` state transition.

### Notifications
- Asynchronous email/SMS delivery queue.
- Attempt counters and retry schedules.
- Maximum five delivery attempts with exponential-style backoff.
- Dedicated Docker Compose worker.

### Certificates
- Event certificate generation after check-in.
- PDF and PNG output.
- Signed-token style public verification using a stored token hash.

### CMS publishing
- Editorial state machine:
  `DRAFT → IN_REVIEW → APPROVED → SCHEDULED → PUBLISHED → ARCHIVED`.
- Scheduled publication execution by the background worker.

### Quality gates
- Fresh Alembic upgrade tested.
- 18 backend tests passing.
- Python compilation validated.
- Frontend source is included; dependency installation/build is delegated to CI because registry access is unavailable in the current build environment.
