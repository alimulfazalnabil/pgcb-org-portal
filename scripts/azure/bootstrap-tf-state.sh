#!/usr/bin/env bash
set -euo pipefail

: "${SUBSCRIPTION_ID:?Set SUBSCRIPTION_ID}"
: "${STATE_LOCATION:=westeurope}"
: "${STATE_RESOURCE_GROUP:=rg-pgcb-tfstate}"
: "${STATE_STORAGE_ACCOUNT:=stpgcbtfstateprod}"
: "${STATE_CONTAINER:=tfstate}"

az account set --subscription "$SUBSCRIPTION_ID"
az group create --name "$STATE_RESOURCE_GROUP" --location "$STATE_LOCATION" --tags Project=pgcb-portal Environment=shared ManagedBy=bootstrap
az storage account create \
  --name "$STATE_STORAGE_ACCOUNT" \
  --resource-group "$STATE_RESOURCE_GROUP" \
  --location "$STATE_LOCATION" \
  --sku Standard_ZRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --https-only true
az storage container create --name "$STATE_CONTAINER" --account-name "$STATE_STORAGE_ACCOUNT" --auth-mode login
az storage account blob-service-properties update --account-name "$STATE_STORAGE_ACCOUNT" --enable-versioning true --delete-retention true --delete-retention-days 30 --auth-mode login

echo "Terraform backend ready: rg=$STATE_RESOURCE_GROUP storage=$STATE_STORAGE_ACCOUNT container=$STATE_CONTAINER key=pgcb-prod.tfstate"
