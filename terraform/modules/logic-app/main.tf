# Terraform module for Azure Logic App
# Sends approval emails and triggers GitHub Actions for approved remediation

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "prefix" {
  type = string
}

variable "github_token" {
  type = string
  sensitive = true
}

variable "github_owner" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "function_app_url" {
  type = string
}

variable "tags" {
  type = map(string)
  default = {}
}

# Logic App (Standard / Consumption)
# Note: Logic App workflows are typically defined in ARM templates or Visual Studio
# This module creates the container for the Logic App

resource "azurerm_logic_app_workflow" "approval_workflow" {
  name                = "${var.prefix}-approval-workflow"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

output "logic_app_id" {
  value = azurerm_logic_app_workflow.approval_workflow.id
}

output "logic_app_name" {
  value = azurerm_logic_app_workflow.approval_workflow.name
}
