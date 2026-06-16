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

  # Workflow definition stored externally or via separate resource
  definition = jsonencode({
    "$schema" = "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#"
    "contentVersion" = "1.0.0.0"
    "triggers" = {
      "When_new_violations_detected" = {
        "type" = "ApiConnection"
        "inputs" = {
          "host" = {
            "connection" = {
              "name" = "@parameters('$connections')['sql']['connectionId']"
            }
          }
          "method" = "get"
          "path" = "/v2/datasets/default/tables/dbo.Violations/items"
          "queries" = {
            "$filter" = "CreatedAt gt adddays(utcNow(),-1)"
          }
        }
      }
    }
    "actions" = {
      "Send_approval_email" = {
        "type" = "ApiConnection"
        "inputs" = {
          "host" = {
            "connection" = {
              "name" = "@parameters('$connections')['office365']['connectionId']"
            }
          }
          "method" = "post"
          "path" = "/Mail"
          "body" = {
            "To" = "@items('For_each_violation').OwnerEmail"
            "Subject" = "Approval Required: Cost Optimization Violation"
            "Body" = "<html><body><p>A cost policy violation has been detected:</p><p>Resource: @{items('For_each_violation').ResourceName}</p><p>Estimated Savings: $@{items('For_each_violation').EstimatedMonthlySavingsUSD}</p></body></html>"
            "Importance" = "High"
          }
        }
      }
    }
  })
}

output "logic_app_id" {
  value = azurerm_logic_app_workflow.approval_workflow.id
}

output "logic_app_name" {
  value = azurerm_logic_app_workflow.approval_workflow.name
}
