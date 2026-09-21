#!/usr/bin/env bash
set -euo pipefail

: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP}"
: "${POSTGRES_SERVER:?Set POSTGRES_SERVER}"
: "${MIN_RETENTION_DAYS:=14}"

read -r retention geo <<<"$(az postgres flexible-server show \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$POSTGRES_SERVER" \
  --query '[backup.backupRetentionDays,backup.geoRedundantBackup]' \
  -o tsv)"

if [[ -z "$retention" || "$retention" -lt "$MIN_RETENTION_DAYS" ]]; then
  echo "ERROR: PostgreSQL backup retention is ${retention:-unknown}; expected at least ${MIN_RETENTION_DAYS} days." >&2
  exit 1
fi

if [[ "${geo,,}" != "enabled" && "${geo,,}" != "true" ]]; then
  echo "ERROR: geo-redundant backup is not enabled." >&2
  exit 1
fi

echo "PostgreSQL backup configuration OK: retention=${retention}d geo_redundant=${geo}"
