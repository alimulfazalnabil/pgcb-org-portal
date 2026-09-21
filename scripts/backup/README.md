# Backup & Recovery Runbook

## Automated control

`verify-postgres-backup.sh` checks that the production PostgreSQL Flexible Server is configured with at least 14 days of retention and geo-redundant backup. The GitHub Actions workflow runs daily.

## Restore drill

Use `restore-drill.sh` during a controlled maintenance window. It creates a temporary Flexible Server from a point-in-time restore. Validate the application schema and read-only queries against the drill server, record the result, then remove the drill resource.

## Operational targets

- Database backup retention: 14 days
- Blob versioning/soft-delete: enabled
- Target RPO: < 1 hour
- Target RTO: < 4 hours
- Production restore drills: quarterly or after major infrastructure changes
