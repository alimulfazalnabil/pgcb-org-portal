# Production Launch Checklist

## Content
- [ ] Replace demo names, committee records and images.
- [ ] Replace demo membership/account data.
- [ ] Confirm Bangla/English terminology with the organization.
- [ ] Upload approved constitution, circulars and journal documents.
- [ ] Confirm footer contact and office-hours data.

## Security
- [ ] Generate production JWT secret.
- [ ] Generate production MFA encryption key.
- [ ] Enable mandatory email verification where policy requires it.
- [ ] Configure production CORS origin.
- [ ] Configure SMTP/SMS provider credentials in Key Vault.
- [ ] Configure payment provider secrets and webhook secrets.
- [ ] Validate CSP against the deployed Next.js asset set.
- [ ] Enable admin MFA for every privileged account.

## Azure
- [ ] Configure Terraform state backend.
- [ ] Run `terraform plan`.
- [ ] Review network/private endpoint settings.
- [ ] Review PostgreSQL backup/HA cost.
- [ ] Configure Front Door custom domain and WAF policy.
- [ ] Configure Application Insights / Log Analytics retention.
- [ ] Configure alert routing.
- [ ] Execute restore drill.

## CI/CD
- [ ] Run API tests.
- [ ] Run web typecheck/build.
- [ ] Run Playwright E2E against staging.
- [ ] Tag release.
- [ ] Deploy to staging.
- [ ] Approve production environment.
- [ ] Deploy production.
- [ ] Verify `/live`, `/ready` and the public homepage.
