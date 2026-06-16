import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

    def _run(command: list[str]) -> dict[str, Any]:
        result = subprocess.run(command, cwd=TERRAFORM_DIR, text=True, capture_output=True)
        return {
            "command": " ".join(command),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    init_result = _run(["terraform", "init"])
    if init_result["returncode"] != 0:
        raise RuntimeError(f"terraform init failed: {init_result['stderr']}")

    plan_result = _run(["terraform", "plan", *tfvars])
    if plan_result["returncode"] != 0:
        raise RuntimeError(f"terraform plan failed: {plan_result['stderr']}")

    apply_result = _run(["terraform", "apply", "-auto-approve", *tfvars])
    if apply_result["returncode"] != 0:
        raise RuntimeError(f"terraform apply failed: {apply_result['stderr']}")

    return {
        "init": init_result,
        "plan": plan_result,
        "apply": apply_result,
    }


def process_expired_windows() -> None:
    store = BlobStore(account_url=BLOB_ACCOUNT_URL)
    now = datetime.now(timezone.utc)

    for blob_name in store.list_blob_names("approval-windows"):
        window = store.read_json("approval-windows", blob_name)
        if _parse_utc_timestamp(window["window_end_utc"]) > now:
            continue

        if window.get("status") in {"processed", "processed_with_errors"}:
            print(f"skipping {blob_name}: already {window.get('status')}")
            continue

        had_errors = False
        did_work = False
        for resource in window.get("resources", []):
            if not resource.get("selected_for_remediation", False):
                continue

            did_work = True
            result_blob_name = f"{resource['violation_id']}.json"

            existing_result = store.read_json_or_none("remediation-results", result_blob_name)
            if existing_result and existing_result.get("status") in {"remediated", "failed"}:
                print(
                    f"skipping violation {resource['violation_id']}: already recorded as "
                    f"{existing_result.get('status')}"
                )
                continue

            try:
                tf_execution = run_terraform(
                    violation_id=resource["violation_id"],
                    remediation_type=resource["remediation_type"],
                    resource_id=resource["resource_id"],
                    recommended_sku=resource.get("recommended_sku") or "",
                )

                store.write_json(
                    "remediation-results",
                    result_blob_name,
                    {
                        "violation_id": resource["violation_id"],
                        "resource_id": resource["resource_id"],
                        "status": "remediated",
                        "estimated_monthly_savings_usd": resource.get("estimated_monthly_savings_usd", 0),
                        "window_id": blob_name.replace(".json", ""),
                        "remediated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "terraform": tf_execution,
                    },
                )
                print(f"remediated violation {resource['violation_id']}")
            except Exception as exc:
                had_errors = True
                store.write_json(
                    "remediation-results",
                    result_blob_name,
                    {
                        "violation_id": resource["violation_id"],
                        "resource_id": resource["resource_id"],
                        "status": "failed",
                        "estimated_monthly_savings_usd": resource.get("estimated_monthly_savings_usd", 0),
                        "window_id": blob_name.replace(".json", ""),
                        "failed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "error": str(exc),
                    },
                )
                print(f"failed remediation for {resource['violation_id']}: {exc}")

        if did_work:
            window["status"] = "processed_with_errors" if had_errors else "processed"
            window["processed_at_utc"] = now.isoformat().replace("+00:00", "Z")
            store.upsert_json("approval-windows", blob_name, window)


if __name__ == "__main__":
    process_expired_windows()
