# Architecture Overview

## Problem
Organizations waste cloud spend due to idle resources, misconfigurations, and policy violations.

## MVP Goal
Detect policy violations across multiple subscriptions, notify app owners via email with approval links, remediate approved actions through Terraform, and display savings.

## Core Flow
1. Scheduled scan runs in AKS CronJob.
2. Policy engine collects Azure resources and evaluates policies.
3. Owner email is resolved from resource tags.
4. Violation record is written to Blob.
5. Policy engine creates owner-specific approval windows in Blob with 7-day expiry.
6. Email with per-resource Remediate links is sent to owner.
7. Approval API updates selected resources in approval-window blobs.
8. Remediation worker CronJob processes expired windows and executes Terraform actions.
9. Savings and execution logs are published for dashboards.

## Services
- Policy Engine: Python scanner and policy evaluator.
- Approval API: FastAPI endpoints for approve and reject links.
- Remediation Worker: Executes Terraform actions after approval.

## Data Stores
- Blob Storage containers:
  - violations
  - approvals
  - remediation-results
  - cost-exports

## Security
- Managed Identity for all Azure access.
- Key Vault for secrets and email provider credentials.
- Least-privilege RBAC per component.

## Real-Time Detection Option
Use Azure Event Grid subscriptions for resource write events. Event Grid triggers a webhook exposed by the Policy Engine. The engine performs targeted scan on changed resources and produces immediate notifications.
