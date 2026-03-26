import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class GCSUploader:
    """Google Cloud Storage file uploader."""

    def __init__(self, bucket_name: str = "", credentials_file: str = "./service_account.json"):
        self.bucket_name = bucket_name
        self.credentials_file = credentials_file
        self._client: object = None
        self._bucket: object = None
        logger.info(f"GCSUploader initialized bucket={bucket_name!r}")

    def _get_client(self):
        """Lazily initialize GCS client."""
        if self._client is not None:
            return self._client
        try:
            from google.cloud import storage
            if os.path.exists(self.credentials_file):
                self._client = storage.Client.from_service_account_json(self.credentials_file)
            else:
                self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
            logger.info("GCS client initialized")
            return self._client
        except Exception as exc:
            logger.error(f"GCS client init failed: {exc}")
            return None

    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """Upload a local file to GCS and return the public URL."""
        client = self._get_client()
        if client is None:
            logger.debug(f"[Mock GCS] upload_file: {local_path} -> {remote_path}")
            return f"https://storage.googleapis.com/{self.bucket_name}/{remote_path}"
        try:
            blob = self._bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            url = self.get_public_url(remote_path)
            logger.info(f"Uploaded {local_path} -> gs://{self.bucket_name}/{remote_path}")
            return url
        except Exception as exc:
            logger.error(f"GCS upload failed {local_path}: {exc}")
            return None

    def upload_image(self, image_bytes: bytes, filename: str) -> Optional[str]:
        """Upload raw image bytes to GCS."""
        client = self._get_client()
        if client is None:
            logger.debug(f"[Mock GCS] upload_image: {filename} ({len(image_bytes)} bytes)")
            return f"https://storage.googleapis.com/{self.bucket_name}/images/{filename}"
        try:
            blob = self._bucket.blob(f"images/{filename}")
            blob.upload_from_string(image_bytes, content_type="image/jpeg")
            url = self.get_public_url(f"images/{filename}")
            logger.info(f"Image uploaded: images/{filename}")
            return url
        except Exception as exc:
            logger.error(f"GCS image upload failed {filename}: {exc}")
            return None

    def get_public_url(self, blob_name: str) -> str:
        """Return the public URL for a GCS blob."""
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from GCS."""
        client = self._get_client()
        if client is None:
            logger.debug(f"[Mock GCS] delete_file: {blob_name}")
            return True
        try:
            blob = self._bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted gs://{self.bucket_name}/{blob_name}")
            return True
        except Exception as exc:
            logger.error(f"GCS delete failed {blob_name}: {exc}")
            return False

    def list_files(self, prefix: str = "") -> List[str]:
        """List files in GCS with an optional prefix filter."""
        client = self._get_client()
        if client is None:
            logger.debug(f"[Mock GCS] list_files prefix={prefix!r}")
            return []
        try:
            blobs = list(self._client.list_blobs(self.bucket_name, prefix=prefix))
            names = [b.name for b in blobs]
            logger.info(f"GCS list {prefix!r}: {len(names)} files")
            return names
        except Exception as exc:
            logger.error(f"GCS list failed prefix={prefix!r}: {exc}")
            return []

    def download_file(self, blob_name: str, local_path: str) -> bool:
        """Download a file from GCS to local disk."""
        client = self._get_client()
        if client is None:
            logger.debug(f"[Mock GCS] download_file: {blob_name} -> {local_path}")
            return False
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            blob = self._bucket.blob(blob_name)
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded gs://{self.bucket_name}/{blob_name} -> {local_path}")
            return True
        except Exception as exc:
            logger.error(f"GCS download failed {blob_name}: {exc}")
            return False
