# API Reference — v0.7

Base URL: `/api/v1`

## Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create member account and blank member profile; issue email-verification token in development |
| POST | `/auth/login` | Validate password/MFA and set a revocable HttpOnly session cookie |
| POST | `/auth/verify-email` | Consume one-time email verification token |
| POST | `/auth/resend-verification` | Issue a new verification token with a non-enumerating response |
| POST | `/auth/logout` | Revoke current session and clear cookie |
| POST | `/auth/logout-all` | Revoke all active sessions |
| GET | `/auth/sessions` | List current user's recent sessions |
| POST | `/auth/sessions/{id}/revoke` | Revoke one owned session |
| GET | `/auth/me` | Return current user and membership summary |
| POST | `/auth/password-reset/request` | Create short-lived password-reset token |
| POST | `/auth/password-reset/confirm` | Consume a reset token and replace password |

## Public

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/public/verify/{membership_id}` | Verify membership by ID |
| GET | `/public/verify-token/{token}` | Verify signed QR token |
| GET | `/public/assets/{filename}` | Serve local public CMS assets |
| GET | `/public/circles` | List active circles |
| GET | `/public/circles/{circle_id}/committee` | Regional committee |
| GET | `/public/committee` | Central executive committee |
| GET | `/public/circulars` | Search/paginate published circulars |
| GET | `/public/journals` | Search/paginate published journals |
| GET | `/public/events` | List events / upcoming events |
| GET | `/public/media` | Filter/paginate public media |
| POST | `/public/contact` | Submit secretariat message |

## Member Portal

Authentication is required.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/member/profile` | Get member profile |
| PATCH | `/member/profile` | Update member profile |
| POST | `/member/application` | Submit membership application |
| GET | `/member/application` | Get application status |
| POST | `/member/documents?document_type=NID` | Upload member document |
| GET | `/member/documents` | List own documents |
| GET | `/member/documents/{id}/download` | Download own document |
| GET | `/member/notifications` | List notifications |
| POST | `/member/notifications/{id}/read` | Mark notification read |
| GET | `/member/card` | Generate PNG membership card |
| GET | `/member/card/pdf` | Generate PDF membership card |
| POST | `/events/{event_id}/registrations/member` | Register authenticated member for an event |
| GET | `/events/registrations/me` | List own event registrations |
| GET | `/member/payments` | List own payment records |
| POST | `/member/payments` | Create payment intent/ledger entry |
| POST | `/member/payments/checkout` | Create provider checkout intent and transaction reference |

## Payment Webhooks

- `POST /payments/webhooks/{provider}` | Receive HMAC-signed provider callback with event-id idempotency

## Certificates

- `POST /certificates/event-registrations/{id}` | Generate certificate after event check-in
- `GET /certificates/verify/{token}` | Public certificate verification
- `GET /certificates/{certificate_no}/download` | Authenticated PDF download

## CMS Workflows

- `GET /admin/workflows` | List content workflow states
- `POST /admin/workflows/{entity_type}/{entity_id}/transition` | Transition CIRCULAR/JOURNAL/EVENT content

## Event Operations

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/events/{event_id}/registrations` | Public event registration |
| GET | `/events/registrations/{ticket_token}` | Verify signed event ticket |
| GET | `/events/registrations/{ticket_token}/qr` | Generate ticket QR image |

## Admin CMS

Permission checks are implemented through the role → permission matrix in `app/core/rbac.py`.

### Dashboard / security

- `GET /admin/stats`
- `GET /admin/permissions`
- `GET /admin/audit-logs`

### Members / documents

- `GET /admin/members`
- `GET /admin/members/{id}`
- `POST /admin/members/{id}/review?action=APPROVE|REJECT|REVIEW|SUSPEND|REACTIVATE`
- `POST /admin/documents/{id}/review?action=APPROVE|REJECT|PENDING`
- `GET /admin/documents/{id}/download`

### CMS entities

CRUD endpoints are available for circulars, circles, committee members, journals, events and media. Event CRUD includes capacity, registration deadline and fee fields.

### Event / finance operations

- `GET /admin/event-registrations`
- `PATCH /admin/event-registrations/{id}`
- `POST /admin/event-registrations/{id}/check-in`
- `POST /admin/event-registrations/check-in-by-ticket`
- `GET /admin/payments`
- `PATCH /admin/payments/{id}`

### Notifications

- `POST /admin/notifications/broadcast`
- `GET /admin/notification-deliveries`
- `GET /admin/certificates`

### User administration / settings

- `GET /admin/users`
- `POST /admin/users`
- `PATCH /admin/users/{id}`
- `GET /admin/settings`
- `PUT /admin/settings`

### Exports

- `GET /admin/exports/members.csv`
- `GET /admin/exports/event-registrations.csv`
- `GET /admin/exports/payments.csv`

Exports are streamed from the database and not persisted as server-side files.

## v1.0 public discovery endpoints

### `GET /api/v1/public/search?q=<term>&limit=<n>`
Searches published circulars, journals, events and media. Private member records are never included.

### `GET /api/v1/public/stats`
Returns public aggregate counts for active members, active circles, published publications and upcoming events.

### `GET /live`
Returns an application liveness response and release version.
