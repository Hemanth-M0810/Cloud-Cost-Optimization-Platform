# Cloud Cost Optimization Platform

Azure-native cost compliance platform built around Azure Policy Insights, Azure Functions, Azure SQL, Terraform, and optional GitHub Actions remediation.

## Current Status

This repository has been migrated away from the older `services/` FastAPI + AKS workflow.
The active implementation now lives under `function-app/` and `terraform/`.

### What currently exists

- Azure Function App code for compliance orchestration and HTTP APIs.
- SQL schema for policies, violations, approvals, remediation executions, and audit logs.
- Terraform modules and env config for:
  - Resource Group
  - Log Analytics
  - Storage
  - Key Vault
  - Azure SQL
  - Function App
  - AKS
- GitHub Actions remediation workflow scaffold.
- Workbook JSON scaffold.

### What is still pending

- Frontend dashboards (violations, approvals, remediation, savings).
- End-to-end approval decision to remediation execution API flow completion.
- Full wiring of all secrets and production runtime settings.
- Optional Logic App workflow finalization.

## Repository Layout (Actual)

```text
.github/
  workflows/
    cd.yml
    ci.yml
    remediation.yml

docs/
  architecture.md
  mvp-policies.md

function-app/
  requirements.txt
  ComplianceOrchestrator/
    function_app.py
    host.json
    local.settings.json
    requirements.txt
    .python_packages/              # local vendored deps for func runtime
    .azurite/                      # local emulator files when used

sql-scripts/
  init.sql

terraform/
  env/
    dev/
      main.tf
      variables.tf
    sandbox/
      main.tf
      outputs.tf
      variables.tf
      terraform.tfvars.example
      README.txt
  modules/
    aks/
    azure-sql/
    function-app/
    logic-app/
  remediation/
    main.tf

workbook/
  compliance-dashboard.json

.env
ImportantCommands.txt
Workflow.txt
```

## Important Note About Old Commands

Do not run:

```powershell
python -m uvicorn services.approval-api.main:app
```

The `services/` folder is no longer present in this repository.

## Local Run (Current, Verified)

### 1. Install function dependencies

```powershell
Set-Location "function-app/ComplianceOrchestrator"
& "../../.venv/Scripts/python.exe" -m pip install -r requirements.txt
& "../../.venv/Scripts/python.exe" -m pip install -r requirements.txt --target ".python_packages/lib/site-packages"
```

### 2. Start local Functions host (API-first mode)

```powershell
Set-Location "function-app/ComplianceOrchestrator"
func start --port 7073
```

Expected output:
- `GetApprovals: [GET] http://localhost:7073/api/approvals`
- `GetViolations: [GET] http://localhost:7073/api/violations`
- `Function ComplianceOrchestrator is disabled.`

The timer trigger is disabled by default in `local.settings.json`:
- `AzureWebJobs.ComplianceOrchestrator.Disabled=true`

This is intentional for local API testing without full storage/timer wiring.

### 3. Test endpoints

```powershell
curl http://localhost:7073/api/violations
curl http://localhost:7073/api/approvals
```

If `SQL_CONNECTION_STRING` is empty, APIs currently return `[]`.

## Troubleshooting Local Runtime

### Port already in use

If 7071/7072/7073 is busy, start on another port:

```powershell
func start --port 7074
```

### Azurite / storage listener errors

If you enable timer trigger and see errors like `127.0.0.1:10000 refused`, storage emulator is not reachable.

Use API-first mode (default timer disabled), or run Azurite and ensure ports are free.

### Function host starts but shows unhealthy storage

This can happen when timer/storage listeners are enabled but local storage is unavailable. HTTP endpoints can still work in API-first mode.

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
  -var="storage_account_name=<globally-unique-storage-name>" \
  -var="key_vault_name_suffix=<globally-unique-kv-suffix>" \
  -var="sql_admin_username=<sql-admin-user>" \
  -var="sql_admin_password=<sql-admin-password>" \
  -var="function_subscription_ids=<comma-separated-subscription-ids>"
```

## Current Data Model

SQL schema is in `sql-scripts/init.sql` and includes:
- `dbo.Policies`
- `dbo.Violations`
- `dbo.Approvals`
- `dbo.RemediationExecutions`
- `dbo.AuditLog`

## Current GitHub Remediation Workflow

Workflow file: `.github/workflows/remediation.yml`

It is scaffolded to:
- accept manual inputs (`approval_id`, `violation_id`, `remediation_type`, `resource_id`)
- login to Azure with OIDC
- run Terraform remediation
- call back Function App status endpoint

Production use still requires complete secret/config wiring.

## Next Build Items

1. Frontend dashboards for violations, approvals, remediations, and realized savings.
2. Decision endpoint wiring (`approve`/`reject`) to remediation trigger/skip path.
3. Savings computation and rollups based on decision + execution status.
4. Azure integration hardening (managed identity permissions, key vault secrets, runtime config).
