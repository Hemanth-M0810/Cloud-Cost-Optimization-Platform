from services.common.blob_store import BlobStore
from services.common.mock_data import generate_sample_violations, generate_sample_approval_windows


class MockBlobStore(BlobStore):
    """
    Mock blob store that returns sample data instead of connecting to Azure.
    Useful for local development and dashboard testing.
    """

    def __init__(self):
        self._violations = generate_sample_violations()
        self._windows = generate_sample_approval_windows()
        self._remediation_results = {}

    def write_json(self, container_name: str, blob_name: str, payload: dict) -> None:
        """Mock write - stores in memory."""
        if container_name == "violations":
            self._violations[blob_name] = payload
        elif container_name == "approval-windows":
            self._windows[blob_name] = payload
        elif container_name == "remediation-results":
            self._remediation_results[blob_name] = payload

    def read_json(self, container_name: str, blob_name: str) -> dict:
        """Mock read - returns from in-memory store."""
        if container_name == "violations":
            if blob_name not in self._violations:
                raise KeyError(f"violation not found: {blob_name}")
            return self._violations[blob_name]
        elif container_name == "approval-windows":
            if blob_name not in self._windows:
                raise KeyError(f"window not found: {blob_name}")
            return self._windows[blob_name]
        elif container_name == "remediation-results":
            if blob_name not in self._remediation_results:
                raise KeyError(f"result not found: {blob_name}")
            return self._remediation_results[blob_name]
        raise KeyError(f"container not found: {container_name}")

    def read_json_or_none(self, container_name: str, blob_name: str) -> dict | None:
        """Mock read or none."""
        try:
            return self.read_json(container_name, blob_name)
        except KeyError:
            return None

    def list_blob_names(self, container_name: str) -> list[str]:
        """Mock list - returns keys from in-memory store."""
        if container_name == "violations":
            return list(self._violations.keys())
        elif container_name == "approval-windows":
            return list(self._windows.keys())
        elif container_name == "remediation-results":
            return list(self._remediation_results.keys())
        return []
