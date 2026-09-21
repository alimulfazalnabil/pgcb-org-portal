# RBAC Model

Roles are intentionally coarse-grained at the database level and fine-grained at the API boundary.

| Role | Main capabilities |
|---|---|
| SUPER_ADMIN | Full platform access |
| CONTENT_EDITOR | Public content, events, journals, media, circles |
| MEMBERSHIP_OFFICER | Members, application review, document review |
| CIRCLE_ADMIN | Circle and member registry access |
| FINANCE_OFFICER | Finance permission namespace (extension point) |
| AUDITOR | Read-only audit/member/content access |
| MEMBER | Own profile, documents, notifications |

Permission checks use `require_permission()` rather than exposing a single universal admin role.

Production recommendation: combine this model with administrator MFA, least-privilege Azure roles, private Blob Storage, WAF/rate limiting and centralized audit ingestion.
