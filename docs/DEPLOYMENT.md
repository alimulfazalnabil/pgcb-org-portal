# Deployment Guide — v0.8

## Local development

### Docker Compose

```bash
docker compose up --build
```

Services:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Worker: background process defined in Compose

### Alembic

```bash
cd services/api
PYTHONPATH=. alembic upgrade head
```

### Seed development content

```bash
cd services/api
python -m app.db.seed
```

Do not use seed credentials in production.

## Azure production architecture

```text
Internet
   |
Azure Front Door + WAF + HTTPS redirect
   |
Web Container App (public ingress)
   |
   +--> API Container App (internal ingress)
   |        |
   |        +--> PostgreSQL Flexible Server (private access)
   |        +--> Redis (private endpoint + TLS)
   |        +--> Blob Storage (private endpoint + managed identity)
   |        +--> Key Vault-backed secrets
   |
   +--> Log Analytics / Application Insights

Worker Container App (no public ingress)
   |
   +--> PostgreSQL / Redis / Blob / notification providers
```

## Terraform

Terraform is under `infrastructure/terraform` and uses the AzureRM remote backend.

Bootstrap the state storage once:

```bash
SUBSCRIPTION_ID=<subscription-id> ./scripts/azure/bootstrap-tf-state.sh
```

Then initialize Terraform using the AzureRM backend environment variables used by `.github/workflows/terraform-apply.yml`.

Production secrets are passed as `TF_VAR_*` values in the protected GitHub `production` environment. The deployed application uses Key Vault secret references rather than putting passwords into application images.

## Workload identity

The Container Apps use dedicated user-assigned managed identities:

```text
ACR           → AcrPull
Key Vault     → Key Vault Secrets User
Blob Storage  → Storage Blob Data Contributor
```

The ACR admin account is disabled. The Storage Account has anonymous access disabled and a private endpoint; its public network endpoint remains enabled so Terraform can provision the private blob container using the provider’s Shared Key management path. Application traffic is intended to resolve and use the private endpoint via the VNet/private DNS path.

## Production application settings

The API can construct its database and Redis connection URLs from discrete environment values:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD      # Key Vault-backed secret

REDIS_HOST
REDIS_PORT
REDIS_PASSWORD   # Key Vault-backed secret
REDIS_SCHEME=rediss
```

Recommended production settings:

```text
APP_ENV=production
FRONTEND_URL=https://<front-door-or-custom-domain>
REQUIRE_EMAIL_VERIFICATION=true
STORAGE_BACKEND=azure
AZURE_STORAGE_ACCOUNT_URL=https://<account>.blob.core.windows.net
AZURE_STORAGE_USE_MANAGED_IDENTITY=true
METRICS_ENABLED=true
```

## Deployment workflow

`deploy-production.yml` builds immutable images in ACR and updates the Web/API/Worker Container Apps.

```text
Git tag / manual dispatch
        |
        v
Azure OIDC login
        |
        +--> ACR build: API/Worker
        +--> ACR build: Web
        |
        v
Container Apps update
        |
        v
Smoke test public web origin
```

The Terraform workflow is deliberately separate from the application release workflow so infrastructure changes can be reviewed independently.

## Domain configuration

The starter currently uses the Front Door-managed endpoint. Before public launch, configure the organization domain on Azure Front Door and update the API `FRONTEND_URL`/CORS allowlist to the final HTTPS origin. Add the organization's DNS CNAME/TXT records using the values shown in the Azure portal.

## Monitoring

- Container Apps environment sends operational logs to Log Analytics.
- Azure Monitor action group sends production alerts to the configured operations email.
- The API provides a protected Prometheus-style `/metrics` endpoint for internal scraping.
- Front Door + WAF forms the internet-facing edge boundary.
- Application Insights is provisioned for request-level instrumentation as the application telemetry layer is expanded.

## Backups and recovery

```bash
AZURE_RESOURCE_GROUP=rg-pgcb-portal \
POSTGRES_SERVER=psql-pgcb-portal \
./scripts/backup/verify-postgres-backup.sh
```

Run the point-in-time restore drill with a dedicated temporary server using `scripts/backup/restore-drill.sh`. The drill server should be removed after validation.

## Payment gateway deployment

Provider-specific calls remain behind `app/integrations/payments.py`.

Before production payments:

1. Implement the selected provider's official API/SDK calls in the adapter.
2. Map exact callback fields into the existing webhook parser.
3. Store provider credentials in Key Vault.
4. Register the public webhook endpoint at the provider.
5. Test success, failure, cancellation, refund and duplicate webhook events in staging.

No live payment credentials are included in this repository.
