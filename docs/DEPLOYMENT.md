# PGCB Organization Portal — Render Staging & Operations Guide

## 1. Render Staging Blueprint Topology (`render.yaml`)

The repository includes an infrastructure-as-code blueprint in [`render.yaml`](../render.yaml) that provisions the Render Staging environment:

1. **`pgcb-portal-api` (FastAPI Backend Web Service)**
   - Root directory: `services/api`
   - Build command: `pip install --upgrade pip && pip install -r requirements.txt`
   - Pre-deploy command: `alembic upgrade head && python -m app.db.seed && python scripts/verify_production_contract.py`
   - Start command: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile -`
   - Health check path: `/health` (and readiness probe at `/ready`)
   - Persistent Disk: `pgcb-uploads` mounted at `/var/data` (`UPLOAD_DIR=/var/data/uploads`)

2. **`pgcb-portal-web` (Next.js 15 Frontend Web Service)**
   - Root directory: `apps/web`
   - Build command: `npm ci && npm run build`
   - Start command: `npm run start`
   - Health check path: `/`
   - Reverse Proxy: Proxies `/backend/:path*` to `INTERNAL_API_URL` (`fromService: pgcb-portal-api`, `property: hostport`) so browser requests remain same-origin and `HttpOnly` session cookies work reliably without cross-site cookie drops.

3. **`pgcb-portal-worker` (Celery Background Worker + Beat)**
   - Root directory: `services/api`
   - Start command: `celery -A app.worker.celery_app worker --beat --loglevel=info --concurrency=2`

4. **`pgcb-portal-redis` (Render Key Value / Redis)**
   - Provides `REDIS_URL` for rate limiting, Celery broker/result backend, and caching.

5. **`pgcb-portal-db` (Render Managed PostgreSQL)**
   - Injects `DATABASE_URL` into `pgcb-portal-api` and `pgcb-portal-worker`.

---

## 2. Environment Variables Reference

### Backend (`pgcb-portal-api` & `pgcb-portal-worker`)
| Variable | Source / Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `staging` (or `production`) | Enables strict staging/production security guards (`Secure` cookies, no predictable demo accounts, no raw reset/verification token responses). |
| `DATABASE_URL` | `fromDatabase: pgcb-portal-db` | PostgreSQL connection string (automatically normalized from `postgres://` to `postgresql+psycopg://`). |
| `REDIS_URL` | `fromService: pgcb-portal-redis` | Redis connection string for rate limiting and Celery worker queues. |
| `JWT_SECRET` | `generateValue: true` | Cryptographic secret (minimum 32 characters) for signing JWT session tokens and verification tokens. |
| `MFA_ENCRYPTION_KEY` | `generateValue: true` | Secret key used to encrypt TOTP MFA secrets at rest. |
| `FRONTEND_URL` | `fromService: pgcb-portal-web (host)` | Automatically normalized to `https://<host>.onrender.com` when a bare hostname is provided by Render. |
| `ALLOWED_ORIGINS` | `fromService: pgcb-portal-web (host)` | CORS origins list (automatically normalized to `https://<host>.onrender.com`). |
| `UPLOAD_DIR` | `/var/data/uploads` | Persistent disk directory for member documents and public assets. |
| `ADMIN_EMAIL` | Render Dashboard Secret (optional) | Bootstrap `SUPER_ADMIN` email used by `python -m app.db.seed` in `staging`/`production`. |
| `ADMIN_PASSWORD` | Render Dashboard Secret (optional) | Bootstrap `SUPER_ADMIN` password (must be $\ge 12$ characters and never a default password). |

### Frontend (`pgcb-portal-web`)
| Variable | Source / Value | Description |
| :--- | :--- | :--- |
| `NODE_ENV` | `production` | Runs Next.js in optimized production server mode. |
| `NEXT_PUBLIC_API_URL` | `/backend` | Browser requests use same-origin `/backend/api/v1/*` proxied by Next.js. |
| `INTERNAL_API_URL` | `fromService: pgcb-portal-api (hostport)` | Internal private network host:port (`http://<host>:<port>`) used by Next.js server-side fetches and `/backend/*` rewrites. |

---

## 3. Initial Admin Account Bootstrap (Staging & Production Security)

Predictable demo accounts (`admin@example.org`, `member@example.org`, `ChangeMe123!`) are **strictly blocked** when `APP_ENV` is `staging` or `production`.

To provision the initial `SUPER_ADMIN` account on Render Staging:
1. **Option A — Environment Variables**: Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` (at least 12 characters) in the `pgcb-portal-api` Environment tab on Render. During `preDeployCommand`, `python -m app.db.seed` will idempotently create or update the bootstrap administrator.
2. **Option B — Render Shell CLI**: Open the Render Shell for `pgcb-portal-api` and run:
   ```bash
   python -m app.scripts.create_admin \
     --email admin@pgcb.org.bd \
     --password "<StrongRandomPassword16+Chars>" \
     --name "কেন্দ্রীয় প্রধান প্রশাসক"
   ```

---

## 4. Render Staging Verification Checklist

After deploying `render-staging-hardening` on Render:
1. **Backend Health**: `GET https://<api-service>.onrender.com/health` returns `{"status":"ok","environment":"staging"}`.
2. **Database Readiness**: `GET https://<api-service>.onrender.com/ready` returns `{"status":"ready","database":"ok"}`.
3. **Frontend Proxy Health**: `GET https://<web-service>.onrender.com/backend/health` returns `200 OK` from FastAPI via Next.js rewrite.
4. **Public Pages**: Verify `/`, `/members`, `/circulars`, `/notices`, `/events`, `/journal`, and `/verify` load without console or CORS errors.
5. **Authentication & RBAC**: Verify login at `/login` sets an `HttpOnly; Secure; SameSite=Lax` cookie, `/member` and `/admin` reject unauthenticated access, and `MEMBER` accounts are denied access to `/admin`.
