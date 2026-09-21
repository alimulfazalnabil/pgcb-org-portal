from __future__ import annotations

import os
from pathlib import Path

from app.services import BASE_STORAGE
from app.core.config import settings


def _safe_name(filename: str) -> str:
    name = Path(filename or 'upload.bin').name.replace(' ', '_')
    return ''.join(ch for ch in name if ch.isalnum() or ch in '._-') or 'upload.bin'


def local_upload(content: bytes, folder: str, filename: str) -> str:
    target_dir = BASE_STORAGE / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / _safe_name(filename)
    target.write_bytes(content)
    return str(target)


def _azure_blob_service():
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError('azure-identity and azure-storage-blob are required for managed-identity storage') from exc

    if settings.azure_storage_connection_string:
        return BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
    if settings.azure_storage_account_url:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        return BlobServiceClient(account_url=settings.azure_storage_account_url, credential=credential)
    raise RuntimeError('Azure Blob Storage is not configured')


def save_bytes(content: bytes, folder: str, filename: str) -> str:
    """Save to Azure Blob with managed identity when configured; otherwise use local development storage."""
    if settings.storage_backend != 'azure':
        return local_upload(content, folder, filename)

    from azure.storage.blob import ContentSettings

    service = _azure_blob_service()
    container = settings.azure_storage_container
    try:
        container_client = service.get_container_client(container)
        if not container_client.exists():
            container_client.create_container()
    except Exception:
        pass

    blob_client = service.get_blob_client(container=container, blob=f'{folder.strip("/")}/{_safe_name(filename)}')
    blob_client.upload_blob(
        content,
        overwrite=True,
        content_settings=ContentSettings(content_type='application/octet-stream'),
    )
    return blob_client.url



def is_local_path(value: str) -> bool:
    try:
        path = Path(value).resolve()
        base = BASE_STORAGE.resolve()
        path.relative_to(base)
        return True
    except Exception:
        return False
