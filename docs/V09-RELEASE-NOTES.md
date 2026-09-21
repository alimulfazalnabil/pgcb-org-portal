# v0.9 Release Notes

## Admin operations

- Permission-aware admin navigation now hides modules the signed-in role cannot access.
- Admin console includes a dedicated operational reports view with six-month membership and event-registration trends.
- Added one-click admin logout.
- Added ticket-code attendance check-in desk to the event registration module.
- Added scheduling UI for CMS publishing.

## CMS workflow hardening

Content workflows now enforce explicit state transitions:

- DRAFT -> IN_REVIEW / PUBLISHED
- IN_REVIEW -> DRAFT / APPROVED
- APPROVED -> IN_REVIEW / SCHEDULED / PUBLISHED
- SCHEDULED -> APPROVED / PUBLISHED
- PUBLISHED -> ARCHIVED
- ARCHIVED -> DRAFT

Scheduled publication must use a future timestamp.

## Public content

- Added circular detail pages.
- Added journal detail pages.
- Added direct detail links from listing pages.

## API

- `GET /api/v1/admin/reports/overview`
- `GET /api/v1/public/circulars/{id}`
- `GET /api/v1/public/journals/{id}`

## Validation

- Backend test suite passes in the build environment.
- Workflow transition, reporting, and public content-detail behavior are covered by v0.9 tests.

## Frontend hardening

- Repaired admin-console JSX nesting in the registrations and audit modules.
- Restricted the admin Security tab to the `settings.read` permission, matching the backend MFA policy.
- Public circular and journal detail routes were syntax-checked with the TypeScript parser.
