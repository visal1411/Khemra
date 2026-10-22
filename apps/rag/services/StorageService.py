import os
import uuid
import boto3
from botocore.config import Config
from django.conf import settings


class StorageService:
    """
    Cloudflare R2 / S3-compatible object storage service.
    Handles presigned PUT upload URL generation and collision-free object keying.
    """

    def __init__(self, s3_client=None):
        self.bucket_name = getattr(settings, "R2_BUCKET_NAME", None) or os.environ.get("R2_BUCKET_NAME", "khemratest")
        self.public_domain = getattr(settings, "R2_PUBLIC_DOMAIN", None) or os.environ.get("R2_PUBLIC_DOMAIN", "pub-d1cf39f6efc3465b9aff3a5e9d49aa54.r2.dev")
        self.endpoint_url = getattr(settings, "R2_ENDPOINT_URL", None) or os.environ.get("R2_ENDPOINT_URL", "")
        self.access_key_id = getattr(settings, "R2_ACCESS_KEY_ID", None) or os.environ.get("R2_ACCESS_KEY_ID", "")
        self.secret_access_key = getattr(settings, "R2_SECRET_ACCESS_KEY", None) or os.environ.get("R2_SECRET_ACCESS_KEY", "")

        # Compute endpoint URL if account ID is set and endpoint_url was not explicitly provided
        if not self.endpoint_url:
            account_id = getattr(settings, "R2_ACCOUNT_ID", None) or os.environ.get("R2_ACCOUNT_ID", "")
            if account_id:
                self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        if s3_client:
            self.s3_client = s3_client
        else:
            client_kwargs = {
                "service_name": "s3",
                "aws_access_key_id": self.access_key_id or "dummy_key",
                "aws_secret_access_key": self.secret_access_key or "dummy_secret",
                "region_name": "auto",
                "config": Config(signature_version="s3v4"),
            }
            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url

            self.s3_client = boto3.client(**client_kwargs)

    def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        folder: str = "documents",
        expires_in: int = 600,
    ) -> dict:
        """
        Generate a cryptographically signed HTTP PUT upload URL for Cloudflare R2 / S3.

        :param filename: Original user filename (e.g., 'report.pdf')
        :param content_type: MIME type (e.g., 'application/pdf', 'video/mp4')
        :param folder: Storage directory prefix (default: 'documents')
        :param expires_in: URL validity window in seconds (default: 600 = 10 minutes)
        :return: dict with upload_url, file_url, key, and expires_in
        """
        # Extract extension safely and lowercase it
        _, ext = os.path.splitext(filename)
        clean_ext = ext.lower().strip()

        # Sanitize folder to avoid path traversal
        clean_folder = folder.strip("/").replace("..", "").replace("\\", "/") or "documents"

        # Unique UUID-based storage key
        unique_key = f"{clean_folder}/{uuid.uuid4()}{clean_ext}"

        # Generate temporary PUT URL
        upload_url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": unique_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

        # Permanent public or CDN read URL
        file_url = f"https://{self.public_domain}/{unique_key}"

        return {
            "upload_url": upload_url,
            "file_url": file_url,
            "key": unique_key,
            "expires_in": expires_in,
        }
