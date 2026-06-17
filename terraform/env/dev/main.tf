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

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.prefix}-law"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
}

resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
}

resource "azurerm_key_vault" "main" {
  name                = "${var.prefix}-kv-${var.key_vault_name_suffix}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = var.tenant_id
  sku_name            = "standard"
}

module "azure_sql" {
  source              = "../../modules/azure-sql"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  prefix              = var.prefix
  admin_username      = var.sql_admin_username
  admin_password      = var.sql_admin_password
}

module "function_app" {
  source                = "../../modules/function-app"
  resource_group_name   = azurerm_resource_group.main.name
  location              = var.location
  prefix                = var.prefix
  subscription_ids      = var.function_subscription_ids
  approval_window_days  = var.approval_window_days
  sql_connection_string = module.azure_sql.connection_string
}

module "aks" {
  source                    = "../../modules/aks"
  name                      = "${var.prefix}-aks"
  location                  = var.location
  resource_group_name       = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  node_vm_size              = var.aks_node_vm_size
  node_count                = var.aks_node_count
}
