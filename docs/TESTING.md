# PGCB Organization Portal — Testing & Verification Guide

## 1. Test Architecture Overview

The repository implements a multi-layered verification strategy covering unit, integration, RBAC matrix, and end-to-end (E2E) workflow tests:

| Test Suite | File Location | Scope |
| :--- | :--- | :--- |
| **Core Portal & Auth Tests** | `services/api/tests/test_portal.py` | Public endpoints, authentication, CSRF protection, member application, QR card verification, MFA, and CSV import/export. |
| **RBAC Permission Matrix** | `services/api/tests/test_rbac_matrix.py` | Exhaustive verification of all 7 roles (`SUPER_ADMIN`, `CONTENT_EDITOR`, `MEMBERSHIP_OFFICER`, `CIRCLE_ADMIN`, `FINANCE_OFFICER`, `AUDITOR`, `MEMBER`) and unauthenticated access against protected endpoints. |
| **End-to-End Domain Workflows** | `services/api/tests/test_workflows_e2e.py` | Full lifecycle tests for Membership (`submit` $\rightarrow$ `approve` $\rightarrow$ `verify`), Events (`create` $\rightarrow$ `register` $\rightarrow$ `check-in`), Certificates (`issue` $\rightarrow$ `verify` $\rightarrow$ `revoke`), and Payments (`initiate` $\rightarrow$ `confirm`). |
| **Notices & Documents CMS** | `services/api/tests/test_notices_documents.py` | CRUD, visibility (`PUBLIC`, `MEMBER`, `ADMIN`), featured filtering, and slug resolution. |
| **Storage & Content Workflow** | `services/api/tests/test_storage_and_workflow.py` | Provider-neutral local/persistent disk storage and editorial state machine transitions (`DRAFT` $\rightarrow$ `REVIEW` $\rightarrow$ `APPROVED` $\rightarrow$ `PUBLISHED`). |
| **Playwright Browser E2E** | `apps/web/e2e/portal.spec.ts` | Browser-level navigation, public search, verification UI, and login flows. |

---

## 2. Running Backend Tests

From `services/api`:

```bash
# Run the complete pytest suite (61 tests)
python -m pytest -v
```

All backend tests run against an isolated test database (`test_portal.db`) configured automatically in `tests/conftest.py`.

---

## 3. Running Frontend Verification

From `apps/web`:

```bash
# 1. TypeScript Static Typecheck
npm run typecheck

# 2. Next.js / ESLint Check
npm run lint

# 3. Production Build Verification
npm run build
```
