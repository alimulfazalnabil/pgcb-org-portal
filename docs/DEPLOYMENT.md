# PGCB Organization Portal — Deployment & Operations Guide

## 1. Render Production Topology

The repository includes an infrastructure-as-code blueprint in `render.yaml` that provisions:
1. **`pgcb-org-api` (Python Web Service)**:
   - Root directory: `services/api`
   - Build command: `pip install -r requirements.txt`
   - Pre-deploy command: `alembic upgrade head`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/api/v1/health/ready`
   - Persistent Disk: Mounted at `/var/data/pgcb-storage` (`STORAGE_BACKEND=persistent_disk`, `STORAGE_ROOT=/var/data/pgcb-storage`)
2. **`pgcb-org-portal` (Node.js Web Service)**:
   - Root directory: `apps/web`
   - Build command: `npm ci && npm run build`
   - Start command: `npm run start -- --hostname 0.0.0.0 --port $PORT`
3. **`pgcb-org-db` (Render Managed PostgreSQL)**:
   - Automatically injects `DATABASE_URL` into `pgcb-org-api`.

---

## 2. Required Environment Variables

### Backend (`services/api`)
| Variable | Description | Production Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment (`development`, `test`, `production`) | `production` |
| `DATABASE_URL` | SQLAlchemy database connection URL | `postgresql+psycopg2://user:pass@host:5432/pgcb` |
| `SECRET_KEY` | Cryptographic secret (minimum 32 characters) for JWT & HMAC signing | `<64-char-random-hex>` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | `https://pgcb-org-portal.onrender.com` |
| `FRONTEND_URL` | Canonical public URL of the Next.js frontend | `https://pgcb-org-portal.onrender.com` |
| `STORAGE_BACKEND` | Storage driver (`local` or `persistent_disk`) | `persistent_disk` |
| `STORAGE_ROOT` | Absolute path to persistent storage directory | `/var/data/pgcb-storage` |
| `COOKIE_SECURE` | Enforce HTTPS-only auth cookies | `true` |

### Frontend (`apps/web`)
| Variable | Description | Production Example |
| :--- | :--- | :--- |
| `BACKEND_INTERNAL_URL` | Backend base URL used by Next.js `/backend/*` rewrites | `https://pgcb-org-api.onrender.com` |
| `NEXT_PUBLIC_SITE_URL` | Public canonical URL of the portal | `https://pgcb-org-portal.onrender.com` |

---

## 3. Initial Admin Bootstrap (Zero Auto-Seed in Production)

Automatic database seeding on application startup is **disabled** to guarantee production data integrity.

To bootstrap the initial `SUPER_ADMIN` account in production or staging, run the dedicated CLI script from `services/api`:

```bash
python -m app.scripts.create_admin \
  --email admin@pgcb.org.bd \
  --password "YourStrongPassword#2026" \
  --name "কেন্দ্রীয় প্রধান প্রশাসক"
```

For local development demo data, you may explicitly invoke the seed module:
```bash
python -c "from app.db.session import SessionLocal; from app.seed import seed_data; db = SessionLocal(); seed_data(db); db.close()"
```
