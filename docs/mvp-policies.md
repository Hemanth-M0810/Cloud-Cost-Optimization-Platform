# MVP Policies

## Initial Policies
1. Unattached managed disks older than threshold.
2. Premium SSD disks with low IO usage recommending SKU downgrade.
3. Missing owner tags for governed subscriptions.

## Remediation Types in MVP
- delete_disk
- change_disk_sku

## Required Tags
- ownerEmail
- application
- costCenter
- environment

## Approval Rules
- High impact actions always require owner approval.
- Approval links expire after configurable TTL.
- Rejected actions are retained with audit reason.
