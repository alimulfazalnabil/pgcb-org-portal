# PGCB Organization Portal — Role-Based Access Control (RBAC)

## 1. Canonical Roles

The portal enforces 7 canonical institutional roles in `services/api/app/core/rbac.py`:

| Role | Institutional Responsibility | Allowed Permissions |
| :--- | :--- | :--- |
| **`SUPER_ADMIN`** | Central Secretariat Chief Administrator | `*` (Full access to all modules, users, settings, MFA, and audit logs) |
| **`CONTENT_EDITOR`** | Publication & Media Secretary | `admin.stats`, `content.read`, `content.write`, `content.publish`, `media.read`, `media.write`, `events.read`, `events.write`, `certificate.write`, `journal.read`, `journal.write`, `circle.read`, `circle.write`, `notice.read`, `notice.write`, `document.read`, `document.write` |
| **`MEMBERSHIP_OFFICER`** | Membership Registrar & Verification Officer | `admin.stats`, `member.read`, `member.review`, `member.write`, `member.import`, `document.read`, `document.write`, `document.review`, `circle.read`, `notification.write`, `certificate.write` |
| **`CIRCLE_ADMIN`** | Regional Grid Circle Coordinator | `admin.stats`, `circle.read`, `circle.write`, `member.read` |
| **`FINANCE_OFFICER`** | Treasurer & Financial Secretary | `admin.stats`, `finance.read`, `finance.write` |
| **`AUDITOR`** | Internal Audit & Compliance Officer | `admin.stats`, `audit.read`, `member.read`, `content.read` |
| **`MEMBER`** | Verified / Applicant Diploma Engineer | `member.self`, `notification.self` |

---

## 2. Role Aliases

For compatibility with external integrations and frontend conventions, `ROLE_ALIASES` maps:
- `ADMIN` $\rightarrow$ `SUPER_ADMIN`
- `EDITOR` $\rightarrow$ `CONTENT_EDITOR`
- `STAFF` $\rightarrow$ `MEMBERSHIP_OFFICER`
- `USER` $\rightarrow$ `MEMBER`

---

## 3. Enforcement Mechanism

1. **Backend API (`require_permission`)**: Every `/api/v1/admin/*` and `/api/v1/workflows/*` endpoint declares its required permission scope via FastAPI `Depends(require_permission('...'))`. Unauthorized requests immediately receive `401 Unauthorized` (if unauthenticated) or `403 Forbidden` (if lacking the required permission).
2. **Frontend Admin Console (`AdminSidebar` & `PermissionGate`)**: The admin layout fetches `/backend/api/v1/admin/permissions` and dynamically filters sidebar links and action controls to match the authenticated user's role.
