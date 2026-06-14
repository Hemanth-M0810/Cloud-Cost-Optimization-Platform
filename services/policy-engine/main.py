import os
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

from services.common.blob_store import BlobStore
from services.common.email_utils import build_owner_approval_email, send_email_placeholder
from services.common.models import ApprovalResourceCandidate, ApprovalWindow, Violation

BLOB_ACCOUNT_URL = os.getenv("BLOB_ACCOUNT_URL", "")
SUBSCRIPTION_IDS = [s.strip() for s in os.getenv("SUBSCRIPTION_IDS", "").split(",") if s.strip()]
APPROVAL_WINDOW_DAYS = int(os.getenv("APPROVAL_WINDOW_DAYS", "7"))
APPROVAL_API_BASE_URL = os.getenv("APPROVAL_API_BASE_URL", "http://approval-api")


def detect_unattached_disks(subscription_id: str) -> List[Violation]:
    credential = DefaultAzureCredential()
    compute = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    violations: List[Violation] = []

    for disk in compute.disks.list():
        if disk.disk_state and disk.disk_state.lower() == "unattached":
            tags = disk.tags or {}
            owner_email = tags.get("ownerEmail", "unknown-owner@example.com")
            violation = Violation(
                violation_id=str(uuid.uuid4()),
                policy_id="disk.unattached",
                subscription_id=subscription_id,
                resource_id=disk.id,
                resource_group=disk.id.split("/")[4],
                owner_email=owner_email,
                remediation_type="delete_disk",
                recommended_sku=None,
                estimated_monthly_savings_usd=15.0,
                status="detected",
                detected_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
            violations.append(violation)
    return violations


def create_owner_windows(store: BlobStore, violations: list[Violation]) -> None:
    by_owner: dict[str, list[Violation]] = defaultdict(list)
    for violation in violations:
        by_owner[violation.owner_email].append(violation)

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=APPROVAL_WINDOW_DAYS)

    for owner_email, owner_violations in by_owner.items():
        window_id = str(uuid.uuid4())
        resources = [
            ApprovalResourceCandidate(
                violation_id=v.violation_id,
                resource_id=v.resource_id,
                remediation_type=v.remediation_type,
                recommended_sku=v.recommended_sku,
                estimated_monthly_savings_usd=v.estimated_monthly_savings_usd,
                selected_for_remediation=False,
            )
            for v in owner_violations
        ]

        window = ApprovalWindow(
            owner_email=owner_email,
            started_at_utc=now.isoformat().replace("+00:00", "Z"),
            window_end_utc=window_end.isoformat().replace("+00:00", "Z"),
            resources=resources,
        )

        window_blob_name = f"{window_id}.json"
        store.write_json("approval-windows", window_blob_name, window.to_dict())

        html = build_owner_approval_email(
            approval_api_base_url=APPROVAL_API_BASE_URL,
            owner_email=owner_email,
            window_id=window_id,
            window_end_utc=window.window_end_utc,
            resources=[r.to_dict() for r in resources],
        )
        send_email_placeholder(
            owner_email=owner_email,
            subject="Action required: cost remediation recommendations",
            html_body=html,
        )


def run_scan() -> None:
    store = BlobStore(account_url=BLOB_ACCOUNT_URL)
    all_violations: list[Violation] = []

    for subscription_id in SUBSCRIPTION_IDS:
        violations = detect_unattached_disks(subscription_id)
        for violation in violations:
            store.write_json("violations", f"{violation.violation_id}.json", violation.to_dict())
            all_violations.append(violation)
            print(f"detected violation {violation.violation_id} in {violation.subscription_id}")

    if all_violations:
        create_owner_windows(store=store, violations=all_violations)


if __name__ == "__main__":
    run_scan()
