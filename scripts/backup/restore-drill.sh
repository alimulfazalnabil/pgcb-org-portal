#!/usr/bin/env bash
set -euo pipefail

: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP}"
: "${POSTGRES_SOURCE_SERVER:?Set POSTGRES_SOURCE_SERVER}"
: "${RESTORE_TARGET_SERVER:?Set RESTORE_TARGET_SERVER}"
: "${RESTORE_TIME:?Set RESTORE_TIME as ISO-8601 UTC timestamp}"
: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD only for a controlled restore drill}"

az postgres flexible-server restore \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$RESTORE_TARGET_SERVER" \
  --source-server "$POSTGRES_SOURCE_SERVER" \
  --restore-time "$RESTORE_TIME" \
  --location "$(az postgres flexible-server show -g "$AZURE_RESOURCE_GROUP" -n "$POSTGRES_SOURCE_SERVER" --query location -o tsv)" \
  --admin-password "$ADMIN_PASSWORD"

echo "Restore drill server created: $RESTORE_TARGET_SERVER"
echo "Validate schema/application connectivity, then delete the drill resource when complete."
