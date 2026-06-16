import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from services.common.blob_store import BlobStore
from services.common.dashboard_utils import aggregate_violations_and_approvals

app = FastAPI(title="approval-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> FileResponse:
    """Serve dashboard HTML."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "../../dashboard/index.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {"message": "dashboard not found, use /dashboard/summary, /dashboard/resources, or /dashboard/savings"}

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

if USE_MOCK_DATA:
    from services.common.mock_blob_store import MockBlobStore
    store = MockBlobStore()
else:
    store = BlobStore(account_url=os.getenv("BLOB_ACCOUNT_URL", ""))


def _parse_utc_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _load_window(window_id: str) -> dict[str, Any]:
    window = store.read_json_or_none("approval-windows", f"{window_id}.json")
    if window is None:
        raise HTTPException(status_code=404, detail=f"approval window not found: {window_id}")
    return window


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/window/{window_id}")
def get_window(window_id: str) -> dict:
    return _load_window(window_id)


@app.get("/window/{window_id}/remediate")
def select_resource_for_remediation(
    window_id: str,
    resource_id: str = Query(...),
    actor: str = Query("owner"),
) -> dict:
    window = _load_window(window_id)

    updated = False
    for resource in window.get("resources", []):
        if resource.get("resource_id") == resource_id:
            resource["selected_for_remediation"] = True
            resource["selected_by"] = actor
            resource["selected_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"resource not found in window: {resource_id}")

    store.upsert_json("approval-windows", f"{window_id}.json", window)

    return {
        "message": "resource marked for remediation",
        "window_id": window_id,
        "resource_id": resource_id,
    }


@app.get("/window/{window_id}/reject")
def reject_resource_remediation(
    window_id: str,
    resource_id: str = Query(...),
    actor: str = Query("owner"),
) -> dict:
    window = _load_window(window_id)

    updated = False
    for resource in window.get("resources", []):
        if resource.get("resource_id") == resource_id:
            resource["selected_for_remediation"] = False
            resource["rejected_by"] = actor
            resource["rejected_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"resource not found in window: {resource_id}")

    store.upsert_json("approval-windows", f"{window_id}.json", window)

    return {
        "message": "resource marked as rejected",
        "window_id": window_id,
        "resource_id": resource_id,
    }


@app.get("/windows/expired")
def list_expired_windows() -> dict:
    now = datetime.now(timezone.utc)
    expired: list[str] = []

    for blob_name in store.list_blob_names("approval-windows"):
        window = store.read_json("approval-windows", blob_name)
        if _parse_utc_timestamp(window["window_end_utc"]) <= now:
            expired.append(blob_name)

    return {"expired_windows": expired}


@app.get("/dashboard/summary")
def get_dashboard_summary() -> dict:
    violations_dict: dict[str, dict[str, Any]] = {}
    for blob_name in store.list_blob_names("violations"):
        violation = store.read_json("violations", blob_name)
        violation_id = violation.get("violation_id")
        if violation_id:
            violations_dict[violation_id] = violation

    windows_dict: dict[str, dict[str, Any]] = {}
    for blob_name in store.list_blob_names("approval-windows"):
        window = store.read_json("approval-windows", blob_name)
        window_dict = dict(window)
        window_dict["window_id"] = blob_name.replace(".json", "")
        windows_dict[blob_name] = window_dict

    aggregated = aggregate_violations_and_approvals(violations_dict, windows_dict)
    return aggregated


@app.get("/dashboard/resources")
def get_resources_for_charting() -> dict:
    summary = get_dashboard_summary()
    resources = summary.get("resources", [])
    return {
        "total": len(resources),
        "by_status": {
            "approved": len([r for r in resources if r["status"] == "approved"]),
            "rejected": len([r for r in resources if r["status"] == "rejected"]),
            "pending": len([r for r in resources if r["status"] == "pending"]),
        },
        "resources": resources,
    }


@app.get("/dashboard/savings")
def get_savings_summary() -> dict:
    summary = get_dashboard_summary()
    resources = summary.get("resources", [])

    total_detected = sum(r.get("estimated_savings_usd", 0) for r in resources)
    total_approved = sum(
        r.get("estimated_savings_usd", 0) for r in resources if r["status"] == "approved"
    )
    total_rejected = sum(
        r.get("estimated_savings_usd", 0) for r in resources if r["status"] == "rejected"
    )
    total_pending = sum(
        r.get("estimated_savings_usd", 0) for r in resources if r["status"] == "pending"
    )

    by_owner = {}
    for r in resources:
        owner = r.get("owner_email", "unknown")
        if owner not in by_owner:
            by_owner[owner] = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}
        by_owner[owner]["total"] += r.get("estimated_savings_usd", 0)
        by_owner[owner][r["status"]] += r.get("estimated_savings_usd", 0)

    return {
        "total_detected_monthly_usd": total_detected,
        "total_approved_monthly_usd": total_approved,
        "total_rejected_monthly_usd": total_rejected,
        "total_pending_monthly_usd": total_pending,
        "by_owner": by_owner,
    }

