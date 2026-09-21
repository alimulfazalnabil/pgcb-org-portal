# Architecture

Browser -> Next.js -> `/backend/*` rewrite -> FastAPI -> PostgreSQL.

Redis is provided in Compose for cache/background jobs. Production target: Azure Front Door/WAF -> Container Apps -> PostgreSQL Flexible Server + Blob Storage + Key Vault + Monitor.

Authentication is JWT in an HttpOnly cookie. Production hardening still requires admin MFA, CSRF protection for mutating operations, rate limiting, upload malware scanning, centralized secrets and formal backup/restore testing.
