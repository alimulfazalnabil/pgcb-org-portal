# PGCB Organization Portal (পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি)

Official Institutional Web Portal, Member Self-Service Platform, Cryptographic Verification System, and Secretariat Administration Console for the **Power Grid Diploma Engineers Association (PGCB)** affiliated with IDEB.

- **Live Production Portal**: [https://pgcb-org-portal.onrender.com](https://pgcb-org-portal.onrender.com)
- **Repository**: [https://github.com/alimulfazalnabil/pgcb-org-portal](https://github.com/alimulfazalnabil/pgcb-org-portal)

---

## 1. Key Capabilities

1. **Public Institutional Website (`apps/web/app/`)**:
   - Bilingual (Bangla-first + English) institutional design system with full dark/light mode support.
   - Dynamic pages for About (`/about`), Executive Committee & Grid Circles (`/committee`, `/committee/message`), Membership Overview & Benefits (`/membership`, `/membership/benefits`), Online Application & Tracking (`/membership/apply`, `/membership/track`), Events & Registration (`/events`, `/events/[id]`), Circulars (`/circulars`), Notices (`/notices`), Documents (`/documents`), Technical Journal (`/journal`), Media Gallery (`/gallery`, `/media`), Unified Search (`/search`), and Contact (`/contact`).
2. **Cryptographic Credential & Certificate Verification**:
   - Digital Member ID Card verification via Member ID or HMAC-SHA256 signed QR token (`/verify`, `/member/verify/[membership_id]`).
   - Digital Certificate verification & PDF download (`/certificates/verify`).
3. **Member Self-Service Portal (`/portal`)**:
   - Authenticated member dashboard with digital ID card, QR verification badge, document uploads, event registrations, and in-app notifications.
4. **Multi-Page Secretariat Administration Console (`/admin/*`)**:
   - 21 specialized subroutes protected by a 7-role RBAC permission matrix (`SUPER_ADMIN`, `CONTENT_EDITOR`, `MEMBERSHIP_OFFICER`, `CIRCLE_ADMIN`, `FINANCE_OFFICER`, `AUDITOR`, `MEMBER`), TOTP MFA, immutable audit logging, and CSV batch import/export.

---

## 2. Architecture & Documentation

Detailed engineering documentation is available in the [`docs/`](./docs) directory:
- [Project Audit & Gap Analysis](./docs/PROJECT_AUDIT.md)
- [Feature Completeness Matrix](./docs/COMPLETENESS_MATRIX.md)
- [System Architecture](./docs/ARCHITECTURE.md)
- [Database Schema & Migrations](./docs/DATABASE.md)
- [Role-Based Access Control (RBAC)](./docs/RBAC.md)
- [Security Architecture](./docs/SECURITY.md)
- [Testing & Verification Guide](./docs/TESTING.md)
- [Deployment & Operations Guide](./docs/DEPLOYMENT.md)

---

## 3. Quick Start (Local Development)

### Backend API (`services/api`)
```bash
cd services/api
python -m venv .venv
# Windows: .\.venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Create an initial SUPER_ADMIN user
python -m app.scripts.create_admin --email admin@pgcb.org.bd --password "StrongPassword#2026"

# Start FastAPI server on port 8000
uvicorn app.main:app --reload --port 8000
```

### Frontend Web (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 4. Quality & Test Verification

```bash
# Backend Test Suite (61 tests)
cd services/api && python -m pytest -v

# Frontend Typecheck, Lint & Production Build
cd apps/web && npm run typecheck && npm run lint && npm run build
```
