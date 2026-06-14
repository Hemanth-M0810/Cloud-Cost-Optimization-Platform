variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name for sandbox resources"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "storage_account_name" {
  description = "Globally unique storage account name"
  type        = string
}

variable "owner_email" {
  description = "Application owner email tag used by policy engine"
  type        = string
}

variable "application_name" {
  description = "Application tag"
  type        = string
  default     = "CloudCostOptimizationPlatform"
}

variable "cost_center" {
  description = "Cost center tag"
  type        = string
  default     = "CC100"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "sandbox"
}

variable "unattached_disk_name" {
  description = "Name of unattached managed disk for policy testing"
  type        = string
  default     = "disk-unattached-demo-01"
}

variable "unattached_disk_size_gb" {
  description = "Disk size in GB"
  type        = number
  default     = 32
}

variable "common_tags" {
  description = "Common tags applied to resources"
  type        = map(string)
  default = {
    project = "cloud-cost-optimization-platform"
    purpose = "terraform-learning"
  }
}
