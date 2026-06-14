import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


def generate_sample_violations() -> dict[str, dict[str, Any]]:
    """Generate sample violation blobs."""
    violations = {}
    
    policies = ["disk.unattached", "disk.low_utilization"]
    subscriptions = ["sub-prod", "sub-staging"]
    owners = ["alice@company.com", "bob@company.com", "charlie@company.com"]
    
    for i in range(12):
        violation_id = str(uuid.uuid4())
        policy = policies[i % len(policies)]
        sub = subscriptions[i % len(subscriptions)]
        owner = owners[i % len(owners)]
        
        violations[violation_id] = {
            "violation_id": violation_id,
            "policy_id": policy,
            "subscription_id": sub,
            "resource_id": f"/subscriptions/{sub}/resourceGroups/rg-{i}/providers/Microsoft.Compute/disks/disk-{i}",
            "resource_group": f"rg-{i}",
            "owner_email": owner,
            "remediation_type": "delete_disk" if policy == "disk.unattached" else "change_disk_sku",
            "recommended_sku": "Standard_LRS" if policy == "disk.low_utilization" else None,
            "estimated_monthly_savings_usd": (15.0 + i * 2) if policy == "disk.unattached" else (8.0 + i),
            "status": "detected",
            "detected_at_utc": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat().replace("+00:00", "Z"),
        }
    
    return violations


def generate_sample_approval_windows() -> dict[str, dict[str, Any]]:
    """Generate sample approval window blobs with mixed approval statuses."""
    windows = {}
    
    violations = generate_sample_violations()
    violation_list = list(violations.items())
    
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=7)
    
    window_id_1 = str(uuid.uuid4())
    window_id_2 = str(uuid.uuid4())
    window_id_3 = str(uuid.uuid4())
    
    windows[f"{window_id_1}.json"] = {
        "owner_email": "alice@company.com",
        "started_at_utc": (now - timedelta(days=2)).isoformat().replace("+00:00", "Z"),
        "window_end_utc": window_end.isoformat().replace("+00:00", "Z"),
        "resources": [
            {
                "violation_id": violation_list[0][0],
                "resource_id": violation_list[0][1]["resource_id"],
                "remediation_type": "delete_disk",
                "recommended_sku": None,
                "estimated_monthly_savings_usd": 15.0,
                "selected_for_remediation": True,
                "selected_by": "alice@company.com",
                "selected_at_utc": (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            },
            {
                "violation_id": violation_list[1][0],
                "resource_id": violation_list[1][1]["resource_id"],
                "remediation_type": "change_disk_sku",
                "recommended_sku": "Standard_LRS",
                "estimated_monthly_savings_usd": 8.0,
                "selected_for_remediation": False,
            },
        ],
    }
    
    windows[f"{window_id_2}.json"] = {
        "owner_email": "bob@company.com",
        "started_at_utc": now.isoformat().replace("+00:00", "Z"),
        "window_end_utc": window_end.isoformat().replace("+00:00", "Z"),
        "resources": [
            {
                "violation_id": violation_list[2][0],
                "resource_id": violation_list[2][1]["resource_id"],
                "remediation_type": "delete_disk",
                "recommended_sku": None,
                "estimated_monthly_savings_usd": 19.0,
                "selected_for_remediation": False,
                "rejected_by": "bob@company.com",
                "rejected_at_utc": now.isoformat().replace("+00:00", "Z"),
            },
            {
                "violation_id": violation_list[3][0],
                "resource_id": violation_list[3][1]["resource_id"],
                "remediation_type": "change_disk_sku",
                "recommended_sku": "Standard_LRS",
                "estimated_monthly_savings_usd": 9.0,
                "selected_for_remediation": True,
                "selected_by": "bob@company.com",
                "selected_at_utc": now.isoformat().replace("+00:00", "Z"),
            },
        ],
    }
    
    windows[f"{window_id_3}.json"] = {
        "owner_email": "charlie@company.com",
        "started_at_utc": now.isoformat().replace("+00:00", "Z"),
        "window_end_utc": window_end.isoformat().replace("+00:00", "Z"),
        "resources": [
            {
                "violation_id": violation_list[4][0],
                "resource_id": violation_list[4][1]["resource_id"],
                "remediation_type": "delete_disk",
                "recommended_sku": None,
                "estimated_monthly_savings_usd": 23.0,
                "selected_for_remediation": False,
            },
            {
                "violation_id": violation_list[5][0],
                "resource_id": violation_list[5][1]["resource_id"],
                "remediation_type": "change_disk_sku",
                "recommended_sku": "Standard_LRS",
                "estimated_monthly_savings_usd": 10.0,
                "selected_for_remediation": False,
            },
        ],
    }
    
    return windows
