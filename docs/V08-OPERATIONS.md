# v0.8 Production Operations

## Azure topology

```text
Azure Front Door + WAF
        |
        v
  Web Container App
        |
        v
  Internal API Container App ----> Private PostgreSQL Flexible Server
        |                           Private DNS / delegated subnet
        +----> Azure Cache for Redis (private endpoint)
        +----> Azure Blob Storage (private endpoint + managed identity)
        +----> Key Vault (RBAC + managed identity)

Worker Container App
        |
        +----> API domain services / PostgreSQL / Redis / Blob / Key Vault

Container Apps Environment ---> Log Analytics
Production alerts -----------> Email Action Group
```

## Identity model

- Container Apps use dedicated user-assigned managed identities.
- ACR access is `AcrPull`; ACR admin credentials are disabled.
- API and Worker receive Key Vault secrets using `Key Vault Secrets User`.
- API and Worker receive Blob permissions using `Storage Blob Data Contributor`.
- PostgreSQL and Redis credentials are not placed in application code.

## Secrets

Terraform requires these sensitive variables:

```text
postgres_admin_password
jwt_secret
mfa_encryption_key
metrics_token
```

Third-party SMTP/SMS/payment credentials should be added as additional Key Vault secrets before enabling those integrations in production. Do not place them in GitHub source or `.env` files committed to the repository.

## Terraform state

Use the AzureRM backend. Bootstrap the state account once:

```bash
SUBSCRIPTION_ID=<subscription-id> ./scripts/azure/bootstrap-tf-state.sh
```

Then initialize Terraform with the backend environment variables documented in the deployment workflow.

## GitHub OIDC

Production workflows use Azure federated identity instead of a long-lived Azure client secret. Configure these GitHub environment secrets:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
TF_STATE_RESOURCE_GROUP
TF_STATE_STORAGE_ACCOUNT
POSTGRES_ADMIN_PASSWORD
JWT_SECRET
MFA_ENCRYPTION_KEY
METRICS_TOKEN
CONTAINER_WEB_IMAGE
CONTAINER_API_IMAGE
CONTAINER_WORKER_IMAGE
ALERT_EMAIL
```

`CONTAINER_*_IMAGE` should reference immutable image tags when Terraform first creates the Container Apps.

## Deployment sequence

1. Bootstrap Terraform state.
2. Create the Azure infrastructure with the Terraform workflow.
3. Build and push container images through `deploy-production.yml` or `az acr build`.
4. Update the Container Apps to the new immutable image SHA.
5. Validate Front Door health and homepage response.
6. Run the Playwright suite against staging before production promotion.
7. Verify backup policy with the scheduled backup workflow.

## Rollback

Container Apps revisions are in single-revision mode in this starter. For an emergency rollback, redeploy the previous immutable image SHA from ACR. A future blue/green rollout can switch `revision_mode` to `Multiple` and move traffic between revisions after adding release orchestration.

## Monitoring

- Container Apps logs are routed to Log Analytics.
- API exposes authenticated `/metrics` for internal Prometheus-compatible scraping.
- An Azure scheduled query rule alerts on repeated `ERROR`, `Traceback`, or `CRITICAL` console logs.
- Front Door/WAF provides the internet-facing edge boundary.
- Application Insights is provisioned for future request-level instrumentation.

## Backup / recovery

- PostgreSQL retention: 14 days.
- PostgreSQL geo-redundant backup: enabled.
- Blob versioning and soft-delete: enabled.
- Run a restore drill quarterly and after major schema/infrastructure changes.
