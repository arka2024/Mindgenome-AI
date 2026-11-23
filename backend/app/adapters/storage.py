from __future__ import annotations

import io
import os
from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger


class StorageAdapter:
    def __init__(self) -> None:
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET
        self.region = settings.S3_REGION
        self.local_fallback_dir = Path("storage_local")
        self.local_fallback_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None

    def _get_client(self):
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url if "minio" in self.endpoint_url or "localhost" in self.endpoint_url else None,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
                )
                # Attempt head_bucket or create bucket
                try:
                    self._s3_client.head_bucket(Bucket=self.bucket)
                except ClientError:
                    try:
                        self._s3_client.create_bucket(Bucket=self.bucket)
                    except Exception:
                        pass
            except Exception as exc:
                logger.warning("s3_client_init_failed_using_local_fallback", error=str(exc))
                self._s3_client = None
        return self._s3_client

    def generate_storage_key(self, user_id: str, document_id: str, filename: str) -> str:
        safe_name = os.path.basename(filename)
        return f"users/{user_id}/documents/{document_id}/{safe_name}"

    def upload_file(self, file_obj: BinaryIO, storage_key: str, content_type: str) -> str:
        """Upload file to S3/MinIO bucket. Falls back to local disk storage if unavailable."""
        client = self._get_client()
        file_obj.seek(0)
        data = file_obj.read()

        if client is not None:
            try:
                client.put_object(
                    Bucket=self.bucket,
                    Key=storage_key,
                    Body=data,
                    ContentType=content_type,
                )
                logger.info("file_uploaded_s3", key=storage_key, bytes=len(data))
                return storage_key
            except Exception as exc:
                logger.error("s3_upload_failed_using_local_fallback", key=storage_key, error=str(exc))

        # Local fallback
        local_path = self.local_fallback_dir / storage_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        logger.info("file_saved_locally", path=str(local_path), bytes=len(data))
        return storage_key

    def download_file(self, storage_key: str) -> bytes:
        """Download file content by storage key."""
        client = self._get_client()
        if client is not None:
            try:
                response = client.get_object(Bucket=self.bucket, Key=storage_key)
                return response["Body"].read()
            except Exception as exc:
                logger.warning("s3_download_failed_checking_local", key=storage_key, error=str(exc))

        # Check local fallback
        local_path = self.local_fallback_dir / storage_key
        if local_path.is_file():
            return local_path.read_bytes()

        raise FileNotFoundError(f"Storage key {storage_key} not found.")

    def delete_file(self, storage_key: str) -> bool:
        """Delete file from storage."""
        deleted = False
        client = self._get_client()
        if client is not None:
            try:
                client.delete_object(Bucket=self.bucket, Key=storage_key)
                deleted = True
            except Exception as exc:
                logger.warning("s3_delete_error", key=storage_key, error=str(exc))

        local_path = self.local_fallback_dir / storage_key
        if local_path.is_file():
            local_path.unlink()
            deleted = True

        return deleted

    def generate_presigned_download_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL for secure temporary download."""
        client = self._get_client()
        if client is not None:
            try:
                return client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": storage_key},
                    ExpiresIn=expires_in,
                )
            except Exception as exc:
                logger.error("presigned_url_failed", key=storage_key, error=str(exc))

        # Local fallback URL
        return f"{settings.API_PUBLIC_URL}/api/v1/documents/download-local?key={storage_key}"


storage_adapter = StorageAdapter()
