import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.common.blob_store import BlobStore

BLOB_ACCOUNT_URL = os.getenv("BLOB_ACCOUNT_URL", "")
TERRAFORM_DIR = Path(os.getenv("TERRAFORM_DIR", REPO_ROOT / "terraform" / "remediation"))


def _parse_utc_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def run_terraform(violation_id: str, remediation_type: str, resource_id: str, recommended_sku: str = "") -> None:
    tfvars = [
        f"-var=violation_id={violation_id}",
        f"-var=remediation_type={remediation_type}",
        f"-var=resource_id={resource_id}",
    ]
    if recommended_sku:
        tfvars.append(f"-var=recommended_sku={recommended_sku}")

    subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)
    subprocess.run(["terraform", "plan", *tfvars], cwd=TERRAFORM_DIR, check=True)
    subprocess.run(["terraform", "apply", "-auto-approve", *tfvars], cwd=TERRAFORM_DIR, check=True)


def process_expired_windows() -> None:
    store = BlobStore(account_url=BLOB_ACCOUNT_URL)
    now = datetime.now(timezone.utc)

    for blob_name in store.list_blob_names("approval-windows"):
        window = store.read_json("approval-windows", blob_name)
        if _parse_utc_timestamp(window["window_end_utc"]) > now:
            continue

        if window.get("status") == "processed":
            continue

        for resource in window.get("resources", []):
            if not resource.get("selected_for_remediation", False):
                continue

            run_terraform(
                violation_id=resource["violation_id"],
                remediation_type=resource["remediation_type"],
                resource_id=resource["resource_id"],
                recommended_sku=resource.get("recommended_sku") or "",
            )

            store.write_json(
                "remediation-results",
                f"{resource['violation_id']}.json",
                {
                    "violation_id": resource["violation_id"],
                    "resource_id": resource["resource_id"],
                    "status": "remediated",
                    "estimated_monthly_savings_usd": resource.get("estimated_monthly_savings_usd", 0),
                    "window_id": blob_name.replace(".json", ""),
                },
            )

        window["status"] = "processed"
        window["processed_at_utc"] = now.isoformat().replace("+00:00", "Z")
        store.upsert_json("approval-windows", blob_name, window)


if __name__ == "__main__":
    process_expired_windows()
