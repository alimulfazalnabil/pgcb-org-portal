# Production Deployment Runbook — PGCB Organization Portal

**Date:** September 29, 2026  
**Repository:** `alimulfazalnabil/pgcb-org-portal`

---

## Option A: One-Click Cloud Deployment via Render Blueprint ([render.yaml](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/render.yaml))

1. In the Render Dashboard, click **New + → Blueprint** and connect `alimulfazalnabil/pgcb-org-portal`.
2. Render automatically provisions:
   - **`pgcb-portal-db`**: Managed PostgreSQL 16 database.
   - **`pgcb-portal-api`**: FastAPI backend with a `5 GB` persistent disk mounted at `/var/data/uploads`, running:
     ```bash
     pip install -r requirements.txt && alembic upgrade head && python -m app.db.seed --production --import-official-members
     ```
   - **`pgcb-portal-web`**: Next.js 15 production web server.
3. Set your initial Super Admin credentials in `pgcb-portal-api` Environment Variables before or after first deploy:
   - `ADMIN_EMAIL=admin@pgcb.org.bd`
   - `ADMIN_PASSWORD=<strong-16+char-password>`
   - `FRONTEND_URL=https://<your-web-domain>`
   - `CORS_ORIGINS=https://<your-web-domain>`

---

## Option B: Docker Compose / HostSeba Linux VPS Deployment

### 1. Prepare Environment Configuration
Copy [.env.production.example](file:///c:/Users/aflna/Downloads/pgcb-org-portal-v1.0/.env.production.example) to `.env.production` and set:
```dotenv
APP_ENV=production
DATABASE_URL=postgresql+psycopg://pgcb_user:<STRONG_DB_PASSWORD>@db:5432/pgcb_portal
SECRET_KEY=<64_CHAR_HEX_SECRET>
MFA_ENCRYPTION_KEY=<FERNET_OR_32_BYTE_KEY>
FRONTEND_URL=https://portal.pgcb.org.bd
CORS_ORIGINS=https://portal.pgcb.org.bd
NEXT_PUBLIC_API_URL=https://api.portal.pgcb.org.bd
STORAGE_DIR=/app/storage
PAYMENT_MODE=sandbox
```

### 2. Build & Start Services
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 3. Run Database Migrations & Seed Official 1,457-Member Dataset
```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.db.seed --production --import-official-members
```

### 4. Verify Health Endpoints
```bash
curl -fsS http://localhost:8000/healthz
curl -fsS http://localhost:8000/readyz
curl -fsS http://localhost:3000/api/health
```

---

## Post-Deployment Verification Checklist

- [ ] `GET /healthz` and `GET /readyz` return `200 OK` with `"database": "ok"`.
- [ ] `GET /api/v1/public/circles` returns all `20` official Diprokous Branch Committees / Grid Circles.
- [ ] `GET /api/v1/public/members` returns `total: 1457` active engineers.
- [ ] `GET /api/v1/public/verify/PGD-2026-0001` returns verified active status for Member #1 without exposing NID/phone.
- [ ] Admin login succeeds with MFA/strong password and `/admin/memberships/applications` loads cleanly.
