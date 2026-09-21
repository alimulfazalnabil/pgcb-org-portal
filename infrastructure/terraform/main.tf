terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}

variable "location" {
  type    = string
  default = "westeurope"
}

variable "project_name" {
  type    = string
  default = "pgcb-portal"
}

variable "postgres_admin_password" {
  type      = string
  sensitive = true
  validation {
    condition     = length(var.postgres_admin_password) >= 20
    error_message = "postgres_admin_password must be at least 20 characters."
  }
}

variable "jwt_secret" {
  type      = string
  sensitive = true
  validation {
    condition     = length(var.jwt_secret) >= 32
    error_message = "jwt_secret must be at least 32 characters."
  }
}

variable "mfa_encryption_key" {
  type      = string
  sensitive = true
}

variable "metrics_token" {
  type      = string
  sensitive = true
  validation {
    condition     = length(var.metrics_token) >= 32
    error_message = "metrics_token must be at least 32 characters."
  }
}

variable "container_web_image" {
  type        = string
  description = "Web OCI image, e.g. myregistry.azurecr.io/pgcb-web:sha-..."
}

variable "container_api_image" {
  type        = string
  description = "API OCI image, e.g. myregistry.azurecr.io/pgcb-api:sha-..."
}

variable "container_worker_image" {
  type        = string
  description = "Worker OCI image, e.g. myregistry.azurecr.io/pgcb-api:sha-..."
}

variable "alert_email" {
  type        = string
  description = "Operations alert recipient."
}

locals {
  tags = {
    Project     = var.project_name
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.40.0.0/20"]
  tags                = local.tags
}

resource "azurerm_subnet" "container_apps" {
  name                 = "snet-container-apps"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.40.0.0/21"]
  delegation {
    name = "container-apps-delegation"
    service_delegation {
      name = "Microsoft.App/environments"
    }
  }
}

resource "azurerm_subnet" "private_endpoints" {
  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.40.3.0/28"]
}

resource "azurerm_subnet" "postgres" {
  name                 = "snet-postgres"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.40.2.0/28"]
  delegation {
    name = "postgres-delegation"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
    }
  }
}

resource "azurerm_private_dns_zone" "postgres" {
  name                = "private.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "link-postgres"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

resource "azurerm_user_assigned_identity" "api" {
  name                = "id-${var.project_name}-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

resource "azurerm_user_assigned_identity" "worker" {
  name                = "id-${var.project_name}-worker"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

resource "azurerm_user_assigned_identity" "web" {
  name                = "id-${var.project_name}-web"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_container_registry" "main" {
  name                = replace("acr${var.project_name}", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = false
  tags                = local.tags
}

resource "azurerm_storage_account" "main" {
  name                            = replace("st${var.project_name}", "-", "")
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true
  blob_properties {
    delete_retention_policy { days = 30 }
    container_delete_retention_policy { days = 30 }
    versioning_enabled = true
  }
  tags = local.tags
}

resource "azurerm_storage_container" "files" {
  name                  = "pgcb-files"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_private_dns_zone" "blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "blob" {
  name                  = "link-blob"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.blob.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

resource "azurerm_private_endpoint" "blob" {
  name                = "pe-blob-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  private_service_connection {
    name                           = "blob-connection"
    private_connection_resource_id = azurerm_storage_account.main.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }
  private_dns_zone_group {
    name                 = "blob-dns"
    private_dns_zone_ids = [azurerm_private_dns_zone.blob.id]
  }
  tags = local.tags
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                          = "psql-${var.project_name}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  version                       = "16"
  administrator_login            = "pgcbadmin"
  administrator_password        = var.postgres_admin_password
  delegated_subnet_id            = azurerm_subnet.postgres.id
  private_dns_zone_id             = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled   = false
  storage_mb                     = 65536
  sku_name                       = "GP_Standard_D2s_v5"
  backup_retention_days          = 14
  geo_redundant_backup_enabled   = true
  zone                           = "1"
  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }
  tags                           = local.tags
  lifecycle {
    prevent_destroy = true
  }
  depends_on                     = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "pgcb_portal"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_redis_cache" "main" {
  name                = "redis-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 1
  family              = "C"
  sku_name            = "Standard"
  minimum_tls_version = "1.2"
  redis_version       = "6"
  tags                = local.tags
}

resource "azurerm_private_dns_zone" "redis" {
  name                = "privatelink.redis.cache.windows.net"
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "redis" {
  name                  = "link-redis"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.redis.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

resource "azurerm_private_endpoint" "redis" {
  name                = "pe-redis-${var.project_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  private_service_connection {
    name                           = "redis-connection"
    private_connection_resource_id = azurerm_redis_cache.main.id
    is_manual_connection           = false
    subresource_names              = ["redisCache"]
  }
  private_dns_zone_group {
    name                 = "redis-dns"
    private_dns_zone_ids = [azurerm_private_dns_zone.redis.id]
  }
  tags = local.tags
}

resource "azurerm_key_vault" "main" {
  name                          = "kv-${replace(var.project_name, "-", "")}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  purge_protection_enabled      = true
  soft_delete_retention_days    = 90
  enable_rbac_authorization     = true
  public_network_access_enabled = true
  tags                          = local.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = var.postgres_admin_password
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "jwt-secret"
  value        = var.jwt_secret
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "mfa_key" {
  name         = "mfa-encryption-key"
  value        = var.mfa_encryption_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "metrics_token" {
  name         = "metrics-token"
  value        = var.metrics_token
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "redis_password" {
  name         = "redis-password"
  value        = azurerm_redis_cache.main.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_container_app_environment" "main" {
  name                           = "cae-${var.project_name}"
  location                       = azurerm_resource_group.main.location
  resource_group_name            = azurerm_resource_group.main.name
  infrastructure_subnet_id       = azurerm_subnet.container_apps.id
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.main.id
  logs_destination               = "log-analytics"
  zone_redundancy_enabled        = true
  tags                            = local.tags
}

resource "azurerm_container_app" "api" {
  name                         = "api-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.api.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.api.id
  }

  secret {
    name                = "jwt-secret"
    key_vault_secret_id = azurerm_key_vault_secret.jwt_secret.id
    identity            = azurerm_user_assigned_identity.api.id
  }
  secret {
    name                = "mfa-key"
    key_vault_secret_id = azurerm_key_vault_secret.mfa_key.id
    identity            = azurerm_user_assigned_identity.api.id
  }
  secret {
    name                = "metrics-token"
    key_vault_secret_id = azurerm_key_vault_secret.metrics_token.id
    identity            = azurerm_user_assigned_identity.api.id
  }
  secret {
    name                = "db-password"
    key_vault_secret_id = azurerm_key_vault_secret.postgres_password.id
    identity            = azurerm_user_assigned_identity.api.id
  }
  secret {
    name                = "redis-password"
    key_vault_secret_id = azurerm_key_vault_secret.redis_password.id
    identity            = azurerm_user_assigned_identity.api.id
  }

  ingress {
    external_enabled = false
    target_port      = 8000
    transport        = "auto"
  }

  template {
    min_replicas = 1
    max_replicas = 5
    container {
      name   = "api"
      image  = var.container_api_image
      cpu    = 1
      memory = "2Gi"
      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "FRONTEND_URL"
        value = "https://${azurerm_cdn_frontdoor_endpoint.main.host_name}"
      }
      env {
        name  = "REQUIRE_EMAIL_VERIFICATION"
        value = "true"
      }
      env {
        name  = "DB_HOST"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = azurerm_postgresql_flexible_server_database.main.name
      }
      env {
        name  = "DB_USER"
        value = "pgcbadmin"
      }
      env {
        name        = "DB_PASSWORD"
        secret_name = "db-password"
      }
      env {
        name        = "JWT_SECRET"
        secret_name = "jwt-secret"
      }
      env {
        name        = "MFA_ENCRYPTION_KEY"
        secret_name = "mfa-key"
      }
      env {
        name        = "METRICS_TOKEN"
        secret_name = "metrics-token"
      }
      env {
        name  = "STORAGE_BACKEND"
        value = "azure"
      }
      env {
        name  = "AZURE_STORAGE_ACCOUNT_URL"
        value = "https://${azurerm_storage_account.main.name}.blob.core.windows.net"
      }
      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = azurerm_storage_container.files.name
      }
      env {
        name  = "REDIS_HOST"
        value = azurerm_redis_cache.main.hostname
      }
      env {
        name  = "REDIS_PORT"
        value = "6380"
      }
      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
      env {
        name  = "REDIS_SCHEME"
        value = "rediss"
      }
      env {
        name  = "REDIS_TLS_VERIFY"
        value = "true"
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
    }
  }
}

resource "azurerm_container_app" "worker" {
  name                         = "worker-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.worker.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.worker.id
  }

  secret {
    name                = "jwt-secret"
    key_vault_secret_id = azurerm_key_vault_secret.jwt_secret.id
    identity            = azurerm_user_assigned_identity.worker.id
  }
  secret {
    name                = "mfa-key"
    key_vault_secret_id = azurerm_key_vault_secret.mfa_key.id
    identity            = azurerm_user_assigned_identity.worker.id
  }
  secret {
    name                = "metrics-token"
    key_vault_secret_id = azurerm_key_vault_secret.metrics_token.id
    identity            = azurerm_user_assigned_identity.worker.id
  }
  secret {
    name                = "db-password"
    key_vault_secret_id = azurerm_key_vault_secret.postgres_password.id
    identity            = azurerm_user_assigned_identity.worker.id
  }
  secret {
    name                = "redis-password"
    key_vault_secret_id = azurerm_key_vault_secret.redis_password.id
    identity            = azurerm_user_assigned_identity.worker.id
  }

  template {
    min_replicas = 1
    max_replicas = 2
    container {
      name    = "worker"
      image   = var.container_worker_image
      command = ["python", "-m", "app.worker"]
      cpu     = 0.5
      memory  = "1Gi"
      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "FRONTEND_URL"
        value = "https://${azurerm_cdn_frontdoor_endpoint.main.host_name}"
      }
      env {
        name  = "REQUIRE_EMAIL_VERIFICATION"
        value = "true"
      }
      env {
        name  = "DB_HOST"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = azurerm_postgresql_flexible_server_database.main.name
      }
      env {
        name  = "DB_USER"
        value = "pgcbadmin"
      }
      env {
        name        = "DB_PASSWORD"
        secret_name = "db-password"
      }
      env {
        name        = "JWT_SECRET"
        secret_name = "jwt-secret"
      }
      env {
        name        = "MFA_ENCRYPTION_KEY"
        secret_name = "mfa-key"
      }
      env {
        name        = "METRICS_TOKEN"
        secret_name = "metrics-token"
      }
      env {
        name  = "STORAGE_BACKEND"
        value = "azure"
      }
      env {
        name  = "AZURE_STORAGE_ACCOUNT_URL"
        value = "https://${azurerm_storage_account.main.name}.blob.core.windows.net"
      }
      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = azurerm_storage_container.files.name
      }
      env {
        name  = "REDIS_HOST"
        value = azurerm_redis_cache.main.hostname
      }
      env {
        name  = "REDIS_PORT"
        value = "6380"
      }
      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }
      env {
        name  = "REDIS_SCHEME"
        value = "rediss"
      }
      env {
        name  = "REDIS_TLS_VERIFY"
        value = "true"
      }
      env {
        name  = "SMTP_HOST"
        value = ""
      }
      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
    }
  }
}

resource "azurerm_container_app" "web" {
  name                         = "web-${var.project_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.web.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.web.id
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 4
    container {
      name   = "web"
      image  = var.container_web_image
      cpu    = 0.5
      memory = "1Gi"
      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "INTERNAL_API_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }
      env {
        name  = "NEXT_PUBLIC_API_BASE_PATH"
        value = "/backend"
      }
    }
  }
}

resource "azurerm_role_assignment" "acr_pull_api" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}
resource "azurerm_role_assignment" "acr_pull_worker" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}
resource "azurerm_role_assignment" "acr_pull_web" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.web.principal_id
}

resource "azurerm_role_assignment" "kv_api" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}
resource "azurerm_role_assignment" "kv_worker" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

resource "azurerm_role_assignment" "storage_api" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}
resource "azurerm_role_assignment" "storage_worker" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

resource "azurerm_monitor_action_group" "ops" {
  name                = "ag-${var.project_name}-ops"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "pgcbops"
  email_receiver {
    name                    = "primary"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }
  tags = local.tags
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "api_errors" {
  name                = "alert-${var.project_name}-api-errors"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  description         = "Alerts when application error traces exceed the production threshold."
  display_name        = "PGCB API application errors"
  enabled             = true
  evaluation_frequency = "PT5M"
  window_duration      = "PT15M"
  scopes               = [azurerm_log_analytics_workspace.main.id]
  severity             = 2
  skip_query_validation = true

  criteria {
    query = <<-QUERY
      ContainerAppConsoleLogs_CL
      | where TimeGenerated > ago(15m)
      | where Log_s has_any ("ERROR", "Traceback", "CRITICAL")
      | summarize ErrorCount = count()
    QUERY
    time_aggregation_method = "Maximum"
    metric_measure_column   = "ErrorCount"
    threshold               = 10
    operator                = "GreaterThan"
    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods              = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.ops.id]
  }
  tags = local.tags
}

resource "azurerm_monitor_diagnostic_setting" "postgres" {
  name                       = "diag-postgres"
  target_resource_id        = azurerm_postgresql_flexible_server.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  enabled_log {
    category = "PostgreSQLLogs"
  }
  metric { category = "AllMetrics" }
}

resource "azurerm_monitor_diagnostic_setting" "storage" {
  name                       = "diag-storage"
  target_resource_id        = azurerm_storage_account.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  metric { category = "Transaction" }
}

resource "azurerm_cdn_frontdoor_profile" "main" {
  name                = "fd-${var.project_name}"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Standard_AzureFrontDoor"
  tags                = local.tags
}

resource "azurerm_cdn_frontdoor_endpoint" "main" {
  name                     = "ep-${var.project_name}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  enabled                  = true
  tags                     = local.tags
}

resource "azurerm_cdn_frontdoor_origin_group" "web" {
  name                     = "og-web"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  session_affinity_enabled = false
  load_balancing {
    additional_latency_in_milliseconds = 0
    sample_size                        = 4
    successful_samples_required        = 3
  }
  health_probe {
    interval_in_seconds = 30
    protocol            = "Https"
    request_type        = "HEAD"
    path                = "/"
  }
}

resource "azurerm_cdn_frontdoor_origin" "web" {
  name                          = "web-origin"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.web.id
  enabled                       = true
  certificate_name_check_enabled = true
  host_name                     = azurerm_container_app.web.ingress[0].fqdn
  origin_host_header            = azurerm_container_app.web.ingress[0].fqdn
  http_port                     = 80
  https_port                    = 443
  priority                      = 1
  weight                        = 1000
}

resource "azurerm_cdn_frontdoor_route" "web" {
  name                          = "route-web"
  cdn_frontdoor_endpoint_id    = azurerm_cdn_frontdoor_endpoint.main.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.web.id
  cdn_frontdoor_origin_ids     = [azurerm_cdn_frontdoor_origin.web.id]
  enabled                      = true
  supported_protocols          = ["Http", "Https"]
  patterns_to_match            = ["/*"]
  forwarding_protocol          = "HttpsOnly"
  link_to_default_domain       = true
  https_redirect_enabled       = true
}

resource "azurerm_cdn_frontdoor_firewall_policy" "main" {
  name                = "waf-${replace(var.project_name, "-", "")}"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = azurerm_cdn_frontdoor_profile.main.sku_name
  enabled             = true
  mode                = "Prevention"
  managed_rule {
    type    = "Microsoft_DefaultRuleSet"
    version = "2.1"
    action  = "Block"
  }
}

resource "azurerm_cdn_frontdoor_security_policy" "main" {
  name                     = "waf-policy"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
  security_policy {
    firewall {
      cdn_frontdoor_firewall_policy_id = azurerm_cdn_frontdoor_firewall_policy.main.id
      association {
        domain {
          cdn_frontdoor_domain_id = azurerm_cdn_frontdoor_endpoint.main.id
        }
        patterns_to_match = ["/*"]
      }
    }
  }
}
