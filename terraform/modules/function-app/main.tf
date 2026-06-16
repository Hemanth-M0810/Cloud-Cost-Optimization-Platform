# Terraform module for Azure Function App
# Deploys the Compliance Orchestrator Function App

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "prefix" {
  type = string
}

variable "subscription_ids" {
  type = string
  description = "Comma-separated list of Azure subscription IDs to scan"
}

variable "approval_window_days" {
  type = number
  default = 7
}

variable "sql_connection_string" {
  type = string
  sensitive = true
}

variable "tags" {
  type = map(string)
  default = {}
}

# Storage Account for Function App
resource "azurerm_storage_account" "function_storage" {
  name                     = "${replace(var.prefix, "-", "")}funcstore"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = var.tags
}

# App Service Plan
resource "azurerm_service_plan" "function_plan" {
  name                = "${var.prefix}-function-plan"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = var.tags
}

# Function App
resource "azurerm_linux_function_app" "orchestrator" {
  name                = "${var.prefix}-compliance-orchestrator"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.function_plan.id
  storage_account_name = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "SUBSCRIPTION_IDS" = var.subscription_ids
    "APPROVAL_WINDOW_DAYS" = var.approval_window_days
    "SQL_CONNECTION_STRING" = var.sql_connection_string
  }

  tags = var.tags

  identity {
    type = "SystemAssigned"
  }
}

output "function_app_id" {
  value = azurerm_linux_function_app.orchestrator.id
}

output "function_app_url" {
  value = azurerm_linux_function_app.orchestrator.default_hostname
}

output "principal_id" {
  value = azurerm_linux_function_app.orchestrator.identity[0].principal_id
}
