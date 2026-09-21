# PGCB Organization Portal — v1.0 Release Candidate

A Bangla-first institutional website, member portal and administrative CMS inspired by the supplied reference screenshots. This release candidate consolidates the public site, membership lifecycle, verification, content workflows, event operations, payment ledger, notifications, security controls and Azure deployment foundation into one deployable platform.

## Release scope

### Public website
- Responsive screenshot-inspired institutional design
- Bangla-first UI with English-ready content fields
- Executive committee and Grid Circle pages
- Circulars / notices / official documents
- Technical journal and publications
- Events and media gallery
- Public membership verification and QR verification
- Public event registration and ticket verification
- Site-wide search across published circulars, journals, events and media
- Dynamic public site statistics API
- Secretariat contact form
- Privacy, terms and accessibility pages

### Member portal
- Registration and login
- Email verification / resend verification
- Password reset
- Profile management
- Membership application workflow
- Secure member document upload/download
- Digital membership card (PNG/PDF) with signed QR verification
- Event registration and ticket access
- Payment history
- Notifications
- Session listing, revocation and logout-all

### Admin / CMS / operations
- KPI and operational reports
- Permission-aware RBAC
- Member search, review, approval, rejection, suspension and reactivation
- Member document review
- Circular, Circle, Committee, Journal, Event and Media CRUD foundations
- Controlled editorial workflow and scheduling
- Event attendance/check-in desk
- Payment status/reconciliation foundation
- Notification delivery queue and logs
- Staff/user management
- Site settings
- Administrator TOTP MFA
- Security audit log
- CSV exports

### Production readiness
- Azure-ready Terraform topology
- PostgreSQL Flexible Server
- Redis
- Blob Storage + managed identity
- Key Vault
- Container Registry + Container Apps
- Front Door + WAF
- Log Analytics + Application Insights
- GitHub OIDC deployment workflow
- Backup verification / restore drill scripts
- Playwright smoke tests
- Liveness / readiness endpoints
- Protected metrics endpoint

## Stack

- Frontend: Next.js 15, React 19, TypeScript, CSS/Tailwind-compatible component styles
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL (SQLite supported for local development)
- Cache/rate limiting: Redis
- Storage: local development or Azure Blob Storage
- Auth/security: JWT + HttpOnly cookies, revocable sessions, TOTP MFA, signed verification tokens
- Infrastructure: Docker, GitHub Actions, Terraform, Azure

## Local development

### Backend

```bash
cd services/api
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000.

API docs: http://localhost:8000/docs

### Docker Compose

```bash
docker compose up --build
```

### Database migrations

```bash
cd services/api
PYTHONPATH=. alembic upgrade head
```

## Demo accounts

- Super Admin: `admin@example.org` / `ChangeMe123!`
- Content Editor: `content@example.org` / `ChangeMe123!`
- Member: `member@example.org` / `ChangeMe123!`
- Demo membership ID: `PGD-2026-1001`

Demo credentials are development-only.

## Frontend routes

```text
/
/search
/committee
/circles
/circles/[circle]
/circulars
/circulars/[id]
/journal
/journal/[id]
/events
/events/[id]
/events/[id]/register
/events/ticket/[token]
/media
/contact
/verify
/certificates/verify
/register
/login
/forgot-password
/reset-password
/verify-email
/resend-verification
/portal
/portal/security
/admin
/privacy
/terms
/accessibility
```

## Operational release checks

Before production:

1. Set production `JWT_SECRET`, `MFA_ENCRYPTION_KEY` and provider credentials through Azure Key Vault.
2. Configure the production domain and Front Door certificate.
3. Run `terraform plan` and review network, backup, WAF and cost settings.
4. Execute a PostgreSQL restore drill and retain the evidence.
5. Run backend tests, frontend typecheck/build and Playwright E2E in CI.
6. Replace demo branding/content and credentials with approved organizational data.

## Verification performed for v1.0 RC

```text
Python compilation: PASS
Fresh Alembic migration: PASS
Backend automated tests: PASS (including new public search/stats/readiness tests)
Frontend source syntax checks: PASS
Docker Compose YAML: PASS
GitHub workflow YAML: PASS
```

A clean Next.js dependency installation/build and Terraform plan cannot be truthfully claimed from this environment because the required npm/Terraform tooling or registry access is not available here. CI remains configured to perform those production checks.

## Security note

The repository contains demo credentials and local development storage only. Before deployment, replace all demo secrets, verify the allowed CORS origin, configure a production CSP after validating the Next.js asset model, enable email verification as appropriate, and configure the selected Bangladesh payment/SMS providers.
