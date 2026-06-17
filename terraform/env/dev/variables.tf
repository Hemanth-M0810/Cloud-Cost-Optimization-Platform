variable "subscription_id" { type = string }
variable "tenant_id" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "prefix" { type = string }
variable "storage_account_name" { type = string }
variable "aks_node_vm_size" {
	type    = string
	default = "Standard_A2_v2"
}
variable "aks_node_count" {
	type    = number
	default = 1
}
variable "key_vault_name_suffix" {
	type    = string
	description = "Suffix for Key Vault name to ensure global uniqueness (e.g., 'dev', 'prod', or a timestamp)"
	default = "dev"
}

variable "sql_admin_username" {
	type        = string
	description = "Azure SQL administrator username"
}

variable "sql_admin_password" {
	type        = string
	sensitive   = true
	description = "Azure SQL administrator password"
}

variable "function_subscription_ids" {
	type        = string
	description = "Comma-separated list of subscription IDs for compliance scans"
}

variable "approval_window_days" {
	type        = number
	description = "Approval window in days for remediation"
	default     = 7
}
