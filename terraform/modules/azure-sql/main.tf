# Terraform module for Azure SQL Database
# Stores audit data, violations, approvals, and remediation results

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "prefix" {
  type = string
}

variable "admin_username" {
  type = string
  sensitive = true
}

variable "admin_password" {
  type = string
  sensitive = true
}

variable "tags" {
  type = map(string)
  default = {}
}

# SQL Server
resource "azurerm_mssql_server" "sql_server" {
  name                         = "${var.prefix}-sqlserver"
  resource_group_name          = var.resource_group_name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.admin_username
  administrator_login_password = var.admin_password

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# SQL Database
resource "azurerm_mssql_database" "compliance_db" {
  name           = "${var.prefix}-compliance-db"
  server_id      = azurerm_mssql_server.sql_server.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  sku_name       = "Basic"
  max_size_gb    = 2

  tags = var.tags
}

# Firewall Rule for Azure Services
resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.sql_server.fully_qualified_domain_name
}

output "database_name" {
  value = azurerm_mssql_database.compliance_db.name
}

output "connection_string" {
  value = "Server=tcp:${azurerm_mssql_server.sql_server.fully_qualified_domain_name},1433;Initial Catalog=${azurerm_mssql_database.compliance_db.name};Persist Security Info=False;User ID=${var.admin_username};Password=${var.admin_password};Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
  sensitive = true
}
