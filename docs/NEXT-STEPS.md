# Next Engineering Steps

The v0.8 baseline now covers the core Azure production topology and operational controls. The next increments should focus on the remaining application-specific launch requirements:

1. Configure the organization's final domain, DNS and Azure Front Door custom domain/certificate.
2. Wire the selected SMTP/SMS and Bangladesh payment providers through Key Vault-backed credentials.
3. Expand Playwright into the full member lifecycle: registration → email verification → membership approval → renewal/payment → event registration → check-in → certificate verification.
4. Add finance reconciliation, settlement reports, refunds and payment exception queues.
5. Add blue/green or canary release orchestration for the Web/API/Worker Container Apps.
6. Add a Bangla-capable certificate font/template and final organizational branding assets.
7. Tighten the production CSP after validating the exact deployed Next.js asset model.
