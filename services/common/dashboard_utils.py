from typing import Any


def aggregate_violations_and_approvals(
    violations_blobs: dict[str, dict[str, Any]],
    windows_blobs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate violations with approval status for dashboard charting.

    Returns:
    {
        "violations_by_policy": {
            "policy_id": {
                "total": int,
                "approved": int,
                "rejected": int,
                "pending": int
            }
        },
        "resources": [
            {
                "policy_id": str,
                "resource_id": str,
                "approved": bool,
                "owner_email": str,
                "estimated_savings_usd": float,
                "status": "approved" | "rejected" | "pending"
            }
        ]
    }
    """

    violations_by_id = violations_blobs
    approval_status = {}

    for window in windows_blobs.values():
        for resource in window.get("resources", []):
            violation_id = resource.get("violation_id")
            approved = resource.get("selected_for_remediation", False)
            approval_status[violation_id] = {
                "approved": approved,
                "rejected": resource.get("rejected_by") is not None,
                "window_id": window.get("window_id"),
            }

    policy_counts: dict[str, dict[str, int]] = {}
    resources_list = []

    for violation_id, violation in violations_by_id.items():
        policy_id = violation.get("policy_id", "unknown")
        resource_id = violation.get("resource_id", "unknown")
        owner_email = violation.get("owner_email", "unknown")
        savings = violation.get("estimated_monthly_savings_usd", 0)

        status_info = approval_status.get(violation_id, {})
        is_approved = status_info.get("approved", False)
        is_rejected = status_info.get("rejected", False)

        if is_approved:
            status = "approved"
        elif is_rejected:
            status = "rejected"
        else:
            status = "pending"

        if policy_id not in policy_counts:
            policy_counts[policy_id] = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}

        policy_counts[policy_id]["total"] += 1
        policy_counts[policy_id][status] += 1

        resources_list.append(
            {
                "policy_id": policy_id,
                "resource_id": resource_id,
                "approved": is_approved,
                "owner_email": owner_email,
                "estimated_savings_usd": savings,
                "status": status,
            }
        )

    return {
        "violations_by_policy": policy_counts,
        "resources": resources_list,
    }
