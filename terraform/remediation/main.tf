terraform {
  required_version = ">= 1.8.0"
  required_providers {
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
  }
}

provider "azapi" {}

variable "violation_id" { type = string }
variable "remediation_type" { type = string }
variable "resource_id" { type = string }
variable "recommended_sku" {
  type    = string
  default = ""
}

locals {
  is_delete_disk     = var.remediation_type == "delete_disk"
  is_change_disk_sku = var.remediation_type == "change_disk_sku"
}

resource "azapi_resource_action" "delete_disk" {
  count       = local.is_delete_disk ? 1 : 0
  resource_id = var.resource_id
  type        = "Microsoft.Compute/disks@2023-10-02"
  action      = "delete"
  method      = "DELETE"
}

resource "azapi_update_resource" "change_disk_sku" {
  count       = local.is_change_disk_sku ? 1 : 0
  resource_id = var.resource_id
  type        = "Microsoft.Compute/disks@2023-10-02"

  body = {
    sku = {
      name = var.recommended_sku
    }
  }
}
