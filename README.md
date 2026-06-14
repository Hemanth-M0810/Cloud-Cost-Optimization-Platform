# Cloud-Cost-Optimization-Platform

An MVP platform that detects cloud cost policy violations across multiple Azure subscriptions, routes approval requests to application owners by email, and performs approved remediations using Terraform.

## What This Solves

Organizations lose money through:
- idle resources
- misconfigured infrastructure
- policy violations

This platform provides:
- violation detection
- owner notification and approval links
- automated remediation with approvals
- savings visibility dashboard inputs

## MVP Decisions Implemented

- Primary approvers: application owners
- Start as MVP, then expand to production
- Remediation types: delete unattached disks and change disk SKU
- Notification channel: email links only for MVP
- Approval model: resource-level remediate selection with a 1-week response window
- Cost baseline: Azure Cost Management exports
- Scope: multiple subscriptions from day one (single tenant)

## Architecture

```text
Azure Resources (VMs, Disks, etc.)
				↓
Python Policy Engine (containerized)
				↓
AKS (CronJob + API services)
				↓
Email Approval Links (Approve / Reject)
				↓
Approval API (FastAPI)
				↓
Blob Storage (violations, approvals, results)
				↓
Terraform Auto-Remediation Worker
				↓
Monitoring + Savings Dashboard Inputs
```

## Repository Structure

```text
docs/
	architecture.md
	mvp-policies.md

services/
	requirements.txt
	common/
		blob_store.py
		models.py
		email_utils.py
		dashboard_utils.py
	policy-engine/
		main.py
		Dockerfile
	approval-api/
		main.py
		Dockerfile
	remediation-worker/
		main.py
		Dockerfile

terraform/
	modules/
		aks/
			main.tf
			variables.tf
	env/
		dev/
			main.tf
			variables.tf
		sandbox/
			main.tf
			variables.tf
			outputs.tf
			terraform.tfvars.example
	remediation/
		main.tf

k8s/
	namespace.yaml
	configmap.yaml
	approval-api-deployment.yaml
	policy-scan-cronjob.yaml
	remediation-window-cronjob.yaml
	hpa-approval-api.yaml

.github/workflows/
	ci.yml
	cd.yml

dashboard/
	index.html
```

## End-to-End Scheduled Scan Flow

1. A scheduled policy scan runs in AKS CronJob.
2. Policy engine inspects resources in each configured subscription.
3. Breaches are identified and owner email is resolved using tags.
4. Violation records are written into Blob container `violations`.
5. Policy engine groups violations per owner and creates an approval-window blob with a 7-day expiry in `approval-windows`.
6. Owner receives an email containing each resource ID and a dedicated `Remediate` link beside it.
7. Clicking `Remediate` marks only that resource in the approval-window blob for auto-remediation.
8. A daily remediation CronJob checks for expired windows and remediates all selected resources.
9. Results are written to Blob container `remediation-results`.
10. Savings data is aggregated with Azure Cost Management exports for dashboarding.

## How Real-Time Detection Works

MVP uses scheduled scans for reliability and simplicity. Real-time can be added in parallel with Event Grid:

1. Configure Event Grid subscription for resource write/update events.
2. Route events to a webhook endpoint on the policy engine.
3. Policy engine performs targeted scan on changed resources only.
4. Violations follow the same approval and remediation pipeline.

This gives low-latency detection while scheduled scans continue as a safety net.

## Step-by-Step Build Process

### 1. Prerequisites

- Azure subscription access for multiple subscriptions
- Terraform >= 1.8
- Azure CLI
- Docker
- kubectl
- Python 3.12

### 2. Provision Core Azure Infrastructure

Use Terraform in `terraform/env/dev` to create:
- Resource Group
- Storage Account
- Key Vault
- Log Analytics Workspace
- AKS Cluster

Example:

```bash
cd terraform/env/dev
terraform init
terraform apply \
	-var="subscription_id=<sub-id>" \
	-var="tenant_id=<tenant-id>" \
	-var="resource_group_name=<rg-name>" \
	-var="location=<region>" \
	-var="prefix=<prefix>" \
	-var="storage_account_name=<storage-account-name>"
```

### 2A. Terraform Learning Sandbox (Recommended First Real Test)

Use the sandbox environment to create only the minimum resources needed for policy testing:
- Resource Group
- Storage Account + required blob containers
- One unattached managed disk with required owner tags

Commands:

```bash
cd terraform/env/sandbox
copy terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your subscription id, storage account name, and owner_email
terraform init
terraform plan
terraform apply
terraform output
```

Important notes:
- `storage_account_name` must be globally unique and lowercase.
- The unattached disk is intentionally created without a VM so policy `disk.unattached` can detect it.
- Keep this sandbox environment isolated from production resources.

### 3. Configure Multi-Subscription Scanning

Set `SUBSCRIPTION_IDS` in `k8s/configmap.yaml` as comma-separated IDs.

Policy engine reads all subscriptions and scans each one in sequence.

For local real-data testing after sandbox apply, set:

```bash
export SUBSCRIPTION_IDS=<sandbox-subscription-id>
export BLOB_ACCOUNT_URL=<blob_account_url_from_terraform_output>
```

### 4. Implement Policy Detection Logic

Current starter policy in `services/policy-engine/main.py` detects unattached disks.

Extend with disk SKU optimization policy by:
- collecting disk metrics
- mapping low-utilization patterns to cheaper SKUs
- writing `change_disk_sku` recommendation with `recommended_sku`

### 5. Add Email Notifications With Resource-Level Approval Links

Policy engine sends one email per owner per scan window.

Email includes one row per breached resource:
- Resource ID
- Remediation type
- `Remediate` button

Link format:
- Remediate selected resource: `/window/<window-id>/remediate?resource_id=<resource-id>&actor=<email>`
- Optional explicit reject link: `/window/<window-id>/reject?resource_id=<resource-id>&actor=<email>`

Store email provider credentials in Key Vault and access with managed identity.

### 6. Process Approvals in Blob During 1-Week Window

Approval API in `services/approval-api/main.py` updates:
- `approval-windows/<window-id>.json`

Each click toggles `selected_for_remediation` for the specific resource. The window remains open for 7 days.

### 7. Execute Remediation via Terraform After Window Expiry

Remediation worker in `services/remediation-worker/main.py`:
- scans `approval-windows` for expired windows
- reads resources marked `selected_for_remediation=true`
- runs Terraform plan/apply in `terraform/remediation`
- applies either:
	- `delete_disk`
	- `change_disk_sku`
- marks window as `processed` to prevent duplicate execution

### 8. Deploy to AKS

Apply Kubernetes manifests:

```bash
kubectl apply -f k8s/
```

MVP includes:
- namespace
- config map
- approval API deployment and service
- periodic scan CronJob
- HPA for API

### 9. Configure CI/CD

- CI: `.github/workflows/ci.yml`
	- Python dependency install
	- Terraform formatting check
	- Python compile checks
	- Docker image builds

- CD: `.github/workflows/cd.yml`
	- Azure login
	- Terraform infrastructure apply
	- AKS credential retrieval
	- Kubernetes deployment

### 10. Build Savings Dashboard Inputs

Approval API exposes three dashboard endpoints:
- `GET /dashboard/summary` — violations by policy with approval counts
- `GET /dashboard/resources` — all resources with policy_id, resource_id, approval status (yes/no), owner_email, savings
- `GET /dashboard/savings` — total detected/approved/rejected/pending savings, broken down by owner

These endpoints return JSON suitable for charting libraries (Chart.js, Plotly, etc.).

Recommended MVP dashboard approach:
1. Frontend (React/Vue or simple HTML+Chart.js) polls these endpoints
2. Display violations by policy and approval status
3. Show savings trends and per-owner breakdown
4. Later: add Azure Workbook or Power BI for advanced analytics

Computations available:
- detected savings
- remediated savings (from remediation-results blobs)
- savings by subscription (parsed from resource_id)
- savings by application owner

## Using Dashboard Endpoints for Charting

Once deployed, the Approval API exposes aggregated data for charting:

```bash
# Get policy violation summary
curl http://approval-api/dashboard/summary

# Get all resources with approval status
curl http://approval-api/dashboard/resources

# Get savings breakdown by owner
curl http://approval-api/dashboard/savings
```

Example frontend (HTML + Chart.js):

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<canvas id="approvalsChart"></canvas>
<script>
  fetch('http://approval-api/dashboard/summary')
    .then(r => r.json())
    .then(data => {
      const policies = Object.keys(data.violations_by_policy);
      const approved = policies.map(p => data.violations_by_policy[p].approved);
      const rejected = policies.map(p => data.violations_by_policy[p].rejected);
      new Chart(document.getElementById('approvalsChart'), {
        type: 'bar',
        data: {
          labels: policies,
          datasets: [
            { label: 'Approved', data: approved },
            { label: 'Rejected', data: rejected }
          ]
        }
      });
    });
</script>
```

### Quick Start Dashboard

A pre-built HTML dashboard is included in `dashboard/index.html`. To use it:

1. Ensure approval-api is running on `http://localhost:8000`
2. Open `dashboard/index.html` in a browser
3. Dashboard displays:
   - Total detected/approved/pending/rejected savings ($)
   - Violations by policy (bar chart)
   - Savings breakdown by status (doughnut chart)
   - Savings by application owner (horizontal bar chart)
   - Pending resources table (top 10)
   - Auto-refreshes every 30 seconds

### Switch From Mock to Real Data

After provisioning sandbox via Terraform:

1. Run policy engine against real Azure resources:

```bash
export SUBSCRIPTION_IDS=<subscription-id>
export BLOB_ACCOUNT_URL=<blob_account_url>
export PYTHONPATH=.
python services/policy-engine/main.py
```

2. Run approval API in real mode:

```bash
cd services/approval-api
export USE_MOCK_DATA=false
export BLOB_ACCOUNT_URL=<blob_account_url>
export PYTHONPATH=../..
uvicorn main:app --reload --port 8000
```

3. Validate detection result:

```bash
curl http://localhost:8000/dashboard/resources
```

You should see the unattached disk resource in the dashboard payload.

## Required Resource Tags

Apply these tags to governed resources:
- `ownerEmail`
- `application`
- `costCenter`
- `environment`

## Security Baseline

- Use managed identity for Azure SDK and storage access
- Keep secrets in Key Vault only
- Grant least-privilege RBAC roles to scanner, API, and remediation worker
- Enable audit logs for approvals and remediation actions

## Roadmap After MVP

1. Add Event Grid based real-time policy checks.
2. Add policy registry and versioned policy packs.
3. Add richer RBAC and approval delegation chains.
4. Add Prometheus metrics and Grafana dashboards.
5. Add stage and prod Terraform environments with gated release promotion.