# integrations/gcs_upload.py
"""Google Cloud Storage upload helper."""
import os
import uuid
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger("gcs_upload")


def _get_client():
    """Return an authenticated GCS client, or None if unavailable."""
    try:
        from google.cloud import storage
        from config.settings import settings

        if settings.GCS_CREDENTIALS_PATH and os.path.exists(settings.GCS_CREDENTIALS_PATH):
            return storage.Client.from_service_account_json(settings.GCS_CREDENTIALS_PATH)
        return storage.Client()
    except Exception as exc:
        logger.error(f"Failed to initialize GCS client: {exc}")
        return None


def upload_image(local_path: str, destination_blob_name: Optional[str] = None) -> Optional[str]:
    """Upload an image file to GCS and return the public URL."""
    from config.settings import settings

    client = _get_client()
    if not client:
        return None

    try:
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        if not destination_blob_name:
            ext = Path(local_path).suffix or ".jpg"
            destination_blob_name = f"products/{uuid.uuid4().hex}{ext}"

        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        blob.make_public()
        public_url = blob.public_url
        logger.info(f"Uploaded {local_path} → {public_url}")
        return public_url
    except Exception as exc:
        logger.error(f"GCS upload failed for {local_path}: {exc}")
        return None


def upload_bytes(image_bytes: bytes, filename: Optional[str] = None, content_type: str = "image/jpeg") -> Optional[str]:
    """Upload raw image bytes to GCS and return the public URL."""
    from config.settings import settings

    client = _get_client()
    if not client:
        return None

    try:
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        if not filename:
            filename = f"products/{uuid.uuid4().hex}.jpg"

        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=content_type)
        blob.make_public()
        return blob.public_url
    except Exception as exc:
        logger.error(f"GCS upload_bytes failed: {exc}")
        return None
