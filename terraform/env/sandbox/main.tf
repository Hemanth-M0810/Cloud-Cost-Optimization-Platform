terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "sandbox" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.common_tags
}

resource "azurerm_storage_account" "sandbox" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.sandbox.name
  location                 = azurerm_resource_group.sandbox.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  tags = var.common_tags
}

resource "azurerm_storage_container" "violations" {
  name                  = "violations"
  storage_account_id    = azurerm_storage_account.sandbox.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "approval_windows" {
  name                  = "approval-windows"
  storage_account_id    = azurerm_storage_account.sandbox.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "remediation_results" {
  name                  = "remediation-results"
  storage_account_id    = azurerm_storage_account.sandbox.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "cost_exports" {
  name                  = "cost-exports"
  storage_account_id    = azurerm_storage_account.sandbox.id
  container_access_type = "private"
}

resource "azurerm_managed_disk" "unattached_demo" {
  name                 = var.unattached_disk_name
  location             = azurerm_resource_group.sandbox.location
  resource_group_name  = azurerm_resource_group.sandbox.name
  storage_account_type = "StandardSSD_LRS"
  create_option        = "Empty"
  disk_size_gb         = var.unattached_disk_size_gb

  tags = merge(
    var.common_tags,
    {
      ownerEmail  = var.owner_email
      application = var.application_name
      costCenter  = var.cost_center
      environment = var.environment
    }
  )
}
