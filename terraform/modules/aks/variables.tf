variable "name" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "log_analytics_workspace_id" { type = string }
variable "node_vm_size" {
	type    = string
	default = "Standard_A2_v2"
}
variable "node_count" {
	type    = number
	default = 1
}
