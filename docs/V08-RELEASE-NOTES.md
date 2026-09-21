# v0.8 Release Notes

## Production Azure & Operations

This release promotes the portal from an application stack to an operations-ready Azure deployment baseline.

### Infrastructure

- Virtual Network and delegated subnets for Container Apps and PostgreSQL.
- Private DNS and private access for PostgreSQL.
- Private endpoints for Azure Blob Storage and Redis.
- Azure Container Registry with managed-identity pulls and admin auth disabled.
- Azure Key Vault with RBAC and dedicated user-assigned Container App identities.
- Web, API, and background Worker Container Apps.
- Azure Front Door with WAF and HTTPS-only routing.
- Log Analytics + Application Insights resources.
- Production action group and log-based application error alert.

### Application operations

- Managed-identity Azure Blob access.
- Runtime database/Redis connection construction from discrete secrets.
- Protected Prometheus-style `/metrics` endpoint.
- Production security settings and verification requirements.

### Automation

- GitHub Actions OIDC-based Terraform workflow.
- ACR build + Container Apps deployment workflow.
- Daily PostgreSQL backup-policy verification.
- Playwright E2E smoke suite.
- Controlled point-in-time restore drill script.

### Validation limitation

Terraform CLI is not installed in the current build environment, so the Azure HCL could not be run through `terraform validate` here. Validate and plan it in CI or a workstation with Terraform 1.6+ and the AzureRM provider before applying to a live subscription.

### Terraform hardening updates

- Terraform targets AzureRM 5.x and uses dedicated user-assigned identities for Container Apps, ACR pulls and Key Vault/Blob access.
- PostgreSQL has `prevent_destroy = true` in Terraform as a safety guard.
- Front Door route caching is disabled by omission of the route cache block so dynamic member/auth API traffic is not unintentionally cached.
- Scheduled-query alert validation is configured to avoid plan-time failure when the Log Analytics table is created dynamically.
- Storage remains non-anonymous with a private endpoint; public network access is retained for Terraform Shared Key data-plane provisioning of the blob container.
