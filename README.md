# Cloud Cost Optimization Platform

Azure-native cost compliance platform using Azure Policy Insights, Azure Functions, Azure SQL, and Terraform.

## Current Repository Layout

```text
function-app/
  ComplianceOrchestrator/
    function_app.py
    host.json
    local.settings.json
    requirements.txt

sql-scripts/
  init.sql

terraform/
  env/
    dev/
      main.tf
      variables.tf
  modules/
    aks/
    azure-sql/
    function-app/
    logic-app/

workbook/
```

## What Changed From Older Docs

This repo no longer contains the old `services/approval-api` FastAPI service.
Do not use commands like:

```powershell
python -m uvicorn services.approval-api.main:app
```

That path does not exist in this repo.

## Local Run (Verified)

### 1. Install Python dependencies

```powershell
Set-Location "function-app/ComplianceOrchestrator"
& "../../.venv/Scripts/python.exe" -m pip install -r requirements.txt
& "../../.venv/Scripts/python.exe" -m pip install -r requirements.txt --target ".python_packages/lib/site-packages"
```

### 2. Start Azure Functions host (API-only mode)

This mode is intended for local endpoint testing and does not require SQL or timer-trigger storage listener.

```powershell
Set-Location "function-app/ComplianceOrchestrator"
func start --port 7073
```

Expected output includes:
- `GetApprovals: [GET] http://localhost:7073/api/approvals`
- `GetViolations: [GET] http://localhost:7073/api/violations`
- `Function ComplianceOrchestrator is disabled.`

### 3. Test endpoints

```powershell
curl http://localhost:7073/api/violations
curl http://localhost:7073/api/approvals
```

If `SQL_CONNECTION_STRING` is not set locally, both endpoints return `[]`.

## Full Local Runtime (Enable Timer Trigger)

By default, timer trigger is disabled in `local.settings.json`:
- `AzureWebJobs.ComplianceOrchestrator.Disabled = true`

To enable it:
1. Set `AzureWebJobs.ComplianceOrchestrator.Disabled` to `false`
2. Ensure `AzureWebJobsStorage` is reachable (Azurite or Azure Storage connection string)
3. Provide `SQL_CONNECTION_STRING` and `SUBSCRIPTION_IDS`

If you see `127.0.0.1:10000 refused`, your storage emulator is not running or port-misaligned.

## Terraform Deployment (Dev)

From `terraform/env/dev`:

```powershell
terraform init
terraform apply \
  -var="subscription_id=<sub-id>" \
  -var="tenant_id=<tenant-id>" \
  -var="resource_group_name=<rg-name>" \
  -var="location=eastus" \
  -var="prefix=<prefix>" \
  -var="storage_account_name=<global-unique-storage-name>" \
  -var="key_vault_name_suffix=<global-unique-kv-suffix>" \
  -var="sql_admin_username=<sql-admin>" \
  -var="sql_admin_password=<sql-password>" \
  -var="function_subscription_ids=<comma-separated-subscriptions>"
```

## Known Notes

- Key Vault names are globally unique. Use `key_vault_name_suffix` to avoid collisions.
- Functions Core Tools may run in offline mode; this is fine if bundle cache already exists.
- If port `7071` is busy, run on another port (`7072`, `7073`, etc.).
