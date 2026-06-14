output "resource_group_name" {
  description = "Sandbox resource group name"
  value       = azurerm_resource_group.sandbox.name
}

output "storage_account_name" {
  description = "Storage account name for blob-backed pipeline"
  value       = azurerm_storage_account.sandbox.name
}

output "blob_account_url" {
  description = "Blob account URL used by services"
  value       = azurerm_storage_account.sandbox.primary_blob_endpoint
}

output "unattached_disk_id" {
  description = "ID of unattached managed disk for policy detection"
  value       = azurerm_managed_disk.unattached_demo.id
}

output "subscription_id" {
  description = "Subscription ID used for deployment"
  value       = var.subscription_id
}
