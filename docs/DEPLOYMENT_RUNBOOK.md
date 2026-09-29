# Production Deployment Runbook — PGCB Organization Portal

**Date:** September 29, 2026  
**Repository:** `alimulfazalnabil/pgcb-org-portal`

---

## Option A: One-Click Cloud Deployment via Render Blueprint ([render.yaml](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/render.yaml))

1. In the Render Dashboard, click **New + → Blueprint** and connect `alimulfazalnabil/pgcb-org-portal`.
2. Render automatically provisions:
   - **`pgcb-portal-db`**: Managed PostgreSQL 16 database.
   - **`pgcb-portal-api`**: FastAPI backend with a `5 GB` persistent disk mounted at `/var/data/uploads` (`STORAGE_BACKEND=persistent_disk`, `STORAGE_ROOT=/var/data/uploads`), `healthCheckPath: /health`, and `preDeployCommand`:
     ```bash
     alembic upgrade head && python -m app.db.seed --production --import-official-members
     ```
   - **`pgcb-portal-web`**: Next.js 15 production web server.
3. Set your initial Super Admin credentials in `pgcb-portal-api` Environment Variables before or after first deploy:
   - `ADMIN_EMAIL=admin@pgcb.org.bd`
   - `ADMIN_PASSWORD=<strong-16+char-password>`
   - `FRONTEND_URL=https://<your-web-domain>`
   - `ALLOWED_ORIGINS=https://<your-web-domain>`

---

## Option B: Docker Compose / HostSeba Linux VPS Deployment ([docker-compose.yml](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/docker-compose.yml))

### 1. Prepare Environment Configuration
Copy [.env.production.example](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/.env.production.example) to `.env` and set:
```dotenv
APP_ENV=production
DATABASE_URL=postgresql+psycopg://pgcb_prod_user:<STRONG_DB_PASSWORD>@postgres:5432/pgcb_portal
JWT_SECRET=<64_CHAR_HEX_SECRET>
MFA_ENCRYPTION_KEY=<FERNET_OR_32_BYTE_KEY>
FRONTEND_URL=https://portal.pgcb.org.bd
ALLOWED_ORIGINS=https://portal.pgcb.org.bd
STORAGE_BACKEND=local
STORAGE_ROOT=/data/uploads
PAYMENT_MODE=sandbox
```

### 2. Build & Start Services
```bash
docker compose up -d --build
```

### 3. Run Database Migrations & Seed Official 1,457-Member Dataset
```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed --production --import-official-members
```

### 4. Verify Health Endpoints
```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/ready
curl -fsS http://localhost:3000/
```

---

## Post-Deployment Verification Checklist

- [ ] `GET /health` (or `/healthz`) and `GET /ready` (or `/readyz`) return `200 OK` with `"database": "ok"`.
- [ ] `GET /api/v1/public/circles` returns all `20` official Diprokous Branch Committees / Grid Circles.
- [ ] `GET /api/v1/public/members` returns `total: 1457` active engineers.
- [ ] `GET /api/v1/public/verify/PGD-2026-0001` returns verified active status for Member #1 without exposing NID/phone.
- [ ] Admin login succeeds with MFA/strong password and `/admin/memberships/applications` loads cleanly.
