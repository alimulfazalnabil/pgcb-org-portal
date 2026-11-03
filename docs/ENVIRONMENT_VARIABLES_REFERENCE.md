# PGCB Organization Portal — Environment Variables Reference
**Release:** `v1.0.0-rc1`  
**Target Environment:** HostSeba cPanel / CloudLinux / Phusion Passenger

This document provides a comprehensive reference for all configuration variables used across the FastAPI backend (`services/api`) and the Next.js frontend (`apps/web`).

---

## 1. Backend API (`services/api`)

These variables are configured in cPanel $\to$ **Setup Python App** $\to$ **Environment variables**, or in `services/api/.env.production`.

| Variable Name | Required | Default Value | Example / Recommended Value | Description |
| :--- | :---: | :--- | :--- | :--- |
| `APP_ENV` | **Yes** | `development` | `production` | Application mode. Use `production` on HostSeba to enforce security validators. |
| `DATABASE_URL` | **Yes** | `sqlite:///./pgcb_portal.db` | `postgresql+psycopg://user:pass@localhost:5432/dbname` | Full Psycopg 3 connection URL. Must use `postgresql+psycopg://`. |
| `DB_HOST` | No | `None` | `localhost` | Database host (used if `DATABASE_URL` is omitted). |
| `DB_PORT` | No | `5432` | `5432` | Database port. |
| `DB_NAME` | No | `pgcb_portal` | `powergri_pgcb_prod` | Database name. |
| `DB_USER` | No | `None` | `powergri_pgcbuser` | Database username. |
| `DB_PASSWORD` | No | `None` | `MySecretPassword123!` | Database password (URL-encoded automatically). |
| `DB_SSLMODE` | No | `prefer` | `prefer` | SSL mode for PostgreSQL connection. |
| `ALLOW_SQLITE_IN_PRODUCTION` | No | `false` | `false` | Safeguard: Must be `false` in production. Only set `true` for emergency SQLite fallback. |
| `ALLOW_STARTUP_FALLBACK` | No | `false` | `false` | If `false`, crashes immediately with masked traceback on misconfiguration. |
| `JWT_SECRET` | **Yes** | *dev-only placeholder* | *(64-character random string)* | Cryptographic key for HS256 JWT tokens. Must be $\ge 32$ characters in production. |
| `SECRET_KEY` | No | `None` | *(same as JWT_SECRET)* | Alias for `JWT_SECRET`. |
| `JWT_EXPIRE_MINUTES` | No | `60` | `60` | Lifespan of access tokens in minutes. |
| `COOKIE_NAME` | No | `pgcb_access_token` | `pgcb_access_token` | Name of the HTTP-only session cookie. |
| `MFA_ENCRYPTION_KEY` | No | `None` | *(32-byte Fernet base64 key)* | Fernet encryption key for MFA TOTP seeds. Generated via Python `Fernet.generate_key()`. |
| `FRONTEND_URL` | **Yes** | `http://localhost:3000` | `https://powergriddiprocoush.org` | Primary frontend web application URL. |
| `ALLOWED_ORIGINS` | No | `None` | `https://powergriddiprocoush.org` | Comma-separated list of allowed CORS and CSRF origins. |
| `STORAGE_BACKEND` | **Yes** | `local` | `local` | File storage driver (`local`, `filesystem`, or `persistent_disk`). |
| `STORAGE_ROOT` | **Yes** | `./storage` | `/home/powergri/storage` | Root directory for file storage (outside public web root). |
| `UPLOAD_DIR` | No | `None` | `/home/powergri/storage/uploads` | Uploaded document storage directory. |
| `MAX_UPLOAD_MB` | No | `5` | `10` | Maximum upload file size in megabytes. |
| `RATE_LIMIT_ENABLED` | No | `true` | `true` | Enables sliding window rate limiting on authentication and sensitive endpoints. |
| `REDIS_RATE_LIMIT_ENABLED` | No | `false` | `false` | Enables Redis-backed distributed rate limiting (leave `false` on shared hosting). |
| `TRUSTED_PROXY_COUNT` | No | `1` | `1` | Number of reverse proxies (LiteSpeed/Passenger) ahead of the FastAPI app. |
| `METRICS_ENABLED` | No | `true` | `true` | Enables `/metrics` Prometheus metrics endpoint. |
| `METRICS_TOKEN` | No | `None` | `secret-token` | Bearer token required to scrape `/metrics` in production. |
| `LOG_LEVEL` | No | `INFO` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `REQUIRE_EMAIL_VERIFICATION`| No | `false` | `true` | Requires email verification before full membership activation. |
| `PASSWORD_RESET_HOURS` | No | `2` | `2` | Password reset token expiration window in hours. |
| `EMAIL_VERIFICATION_HOURS` | No | `24` | `24` | Email verification token expiration window in hours. |
| `SMTP_HOST` | No | `None` | `mail.powergriddiprocoush.org` | SMTP server for outgoing emails. |
| `SMTP_PORT` | No | `587` | `587` | SMTP port (587 for STARTTLS, 465 for SSL). |
| `SMTP_USERNAME` | No | `None` | `noreply@powergriddiprocoush.org` | SMTP username. |
| `SMTP_PASSWORD` | No | `None` | *(cPanel email password)* | SMTP password. |
| `SMTP_FROM` | No | `None` | `PGCB Secretariat <noreply@powergriddiprocoush.org>` | Outgoing sender display name and email. |
| `PAYMENT_MODE` | No | `sandbox` | `sandbox` | Payment mode: `sandbox` (for test transactions) or `live`. |
| `PAYMENT_WEBHOOK_SECRET` | No | `None` | `secret` | Shared secret for verifying payment gateway webhooks. |
| `BKASH_APP_KEY` | No | `None` | `app-key` | bKash tokenized checkout credentials. |
| `BKASH_APP_SECRET` | No | `None` | `app-secret` | bKash secret. |
| `BKASH_USERNAME` | No | `None` | `username` | bKash username. |
| `BKASH_PASSWORD` | No | `None` | `password` | bKash password. |
| `SSLCOMMERZ_STORE_ID` | No | `None` | `store-id` | SSLCommerz store ID. |
| `SSLCOMMERZ_STORE_PASSWORD` | No | `None` | `store-pass` | SSLCommerz store password. |
| `NAGAD_MERCHANT_ID` | No | `None` | `merchant-id` | Nagad merchant ID. |

---

## 2. Frontend Web Application (`apps/web`)

These variables are configured in `apps/web/.env.production` or during the Next.js build.

| Variable Name | Required | Default Value | Example / Recommended Value | Description |
| :--- | :---: | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_PATH` | No | `/backend` | `/backend` | Browser-visible API base path. Browser requests route to `/backend` and are rewritten server-side. |
| `INTERNAL_API_URL` | **Yes** | `http://localhost:8000` | `https://api.powergriddiprocoush.org` | Backend target URL for Next.js server-side rewrites and SSR. |
| `NEXT_PUBLIC_API_URL` | No | `None` | `https://api.powergriddiprocoush.org` | Optional public API URL fallback. |
| `NEXT_PUBLIC_SITE_URL` | **Yes** | `http://localhost:3000` | `https://powergriddiprocoush.org` | Canonical public URL of the website. |
