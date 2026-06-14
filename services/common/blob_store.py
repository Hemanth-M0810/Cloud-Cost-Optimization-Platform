import json
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class BlobStore:
    def __init__(self, account_url: str):
        self._client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

    def write_json(self, container_name: str, blob_name: str, payload: dict) -> None:
        container = self._client.get_container_client(container_name)
        if not container.exists():
            container.create_container()
        container.upload_blob(blob_name, json.dumps(payload), overwrite=True)

    def upsert_json(self, container_name: str, blob_name: str, payload: dict) -> None:
        self.write_json(container_name, blob_name, payload)

    def read_json(self, container_name: str, blob_name: str) -> dict:
        blob = self._client.get_blob_client(container=container_name, blob=blob_name)
        data = blob.download_blob().readall().decode("utf-8")
        return json.loads(data)

    def read_json_or_none(self, container_name: str, blob_name: str) -> dict | None:
        try:
            return self.read_json(container_name, blob_name)
        except ResourceNotFoundError:
            return None

    def list_blob_names(self, container_name: str) -> list[str]:
        container = self._client.get_container_client(container_name)
        if not container.exists():
            return []
        return [blob.name for blob in container.list_blobs()]
