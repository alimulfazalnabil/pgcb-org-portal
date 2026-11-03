# Source of Truth and Deployment Policy

## 1. Canonical source

The GitHub repository `alimulfazalnabil/pgcb-org-portal` is the single source of truth for application source code and deployment configuration.

- Production source branch: `main`
- Repository: https://github.com/alimulfazalnabil/pgcb-org-portal
- Only reviewed and committed files on `main` are eligible for production deployment.
- HostSeba cPanel files are deployment copies. They must not become an independent source of truth.
- A production deployment must record the exact Git commit SHA that was deployed.

## 2. Change workflow

1. Make changes in a feature branch or approved development environment.
2. Run the relevant backend, frontend, type, lint, migration and security checks.
3. Review the diff for accidental secrets, personal data, generated files and local-only configuration.
4. Merge approved changes into `main`.
5. Deploy the exact `main` commit to HostSeba.
6. Verify frontend, API liveness, API readiness, authentication, uploads and critical user journeys.
7. Record the deployed commit SHA and deployment date.

Do not edit production application files directly in cPanel except for an approved emergency recovery. Any emergency change must be copied back into GitHub, reviewed, tested and committed before the next deployment.

## 3. Production configuration and secrets

The repository contains code and safe configuration templates only. Never commit:

- `.env`, `.env.production`, credentials or database connection strings
- PostgreSQL passwords, JWT signing keys, MFA encryption keys or API tokens
- Private keys, certificates, session secrets or payment-provider secrets
- Production database dumps, member records, uploaded documents or backups

Store production values in the HostSeba cPanel Python/Node application environment configuration or another approved secret manager. Keep only placeholders and documentation in tracked example files.

The production database and user-uploaded data are operational state, not source code. Deployments must not overwrite, reset or delete them.

## 4. HostSeba deployment boundary

HostSeba is the production runtime. It executes the application files present in the configured cPanel application roots. A GitHub commit does not update HostSeba unless a deployment operation is performed.

Before deploying, confirm:

- The cPanel Python application's Application Root and Startup File point to the intended repository deployment directory.
- The deployed files match the intended Git commit.
- Dependencies are installed for the configured Python/Node runtime.
- Required environment variables are configured outside Git.
- Database migrations are reviewed and backed up before execution.
- Writable upload/storage paths are outside the code checkout where practical.
- The Passenger application is restarted after code/dependency changes.

Do not assume that a GitHub push automatically deploys to HostSeba. Automatic deployment may only be enabled after a secure deployment method and credentials are explicitly configured and tested.

## 5. Branch and release discipline

- Treat `main` as the production-ready branch.
- Prefer pull requests for non-trivial changes.
- Do not force-push or rewrite the production branch history.
- Do not commit directly to `main` for routine work.
- Use descriptive commits and keep changes reviewable.
- Tag or record production releases with the commit SHA.
- Enable GitHub branch protection/rulesets for `main` in repository settings where the GitHub plan permits it.

Recommended required checks before merging:
- Backend unit and integration tests
- Frontend lint and type checking
- Frontend production build
- Dependency/security scanning
- Migration validation
- Secret scanning

## 6. Recovery and rollback

Before a production deployment, record the currently deployed commit SHA and take/verify a database backup according to the operational backup policy.

If a deployment fails:
1. Stop further deployment attempts.
2. Inspect application and Passenger logs.
3. Restore the last known-good code revision.
4. Do not roll back or modify database schema/data blindly; database rollback requires a migration-specific recovery plan.
5. Verify readiness and critical workflows.
6. Document the incident and corrective change in GitHub.

## 7. Deployment record

For every production deployment, record:

| Field | Value |
|---|---|
| Environment | HostSeba production |
| Source branch | `main` |
| Commit SHA | Exact deployed SHA |
| Deployment time | UTC timestamp |
| Deployed by | Operator or automation identity |
| Database backup | Backup identifier/status |
| Verification | PASS / FAIL with evidence |
| Rollback revision | Previous known-good SHA |

## 8. Current automation status

This policy establishes GitHub `main` as the canonical source. It does not by itself configure HostSeba auto-deployment, cPanel Git Version Control, GitHub Actions secrets, or branch protection settings. Those must be configured and verified separately. Until then, deployment is a controlled manual operation from a known GitHub commit.
