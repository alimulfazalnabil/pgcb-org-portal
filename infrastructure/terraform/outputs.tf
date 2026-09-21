output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "registry_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "storage_account" {
  value = azurerm_storage_account.main.name
}

output "postgres_server" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "web_url" {
  value = "https://${azurerm_cdn_frontdoor_endpoint.main.host_name}"
}

output "web_origin_url" {
  value = "https://${azurerm_container_app.web.ingress[0].fqdn}"
}

output "api_internal_url" {
  value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}
