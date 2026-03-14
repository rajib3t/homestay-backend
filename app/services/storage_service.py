from typing import Optional
import boto3
from aioboto3 import Session
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageService:
    """Simple S3-compatible storage service supporting AWS S3 and MinIO via endpoint URL.

    Usage: configure S3 settings in environment (.env) and inject via deps.
    """

    def __init__(self):
        self.session = Session()
        self.bucket: Optional[str] = settings.S3_BUCKET
        self.client_params = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
        }
        # optional endpoint for MinIO or other S3-compatible services
        if settings.S3_ENDPOINT_URL:
            self.client_params["endpoint_url"] = settings.S3_ENDPOINT_URL
        # boto3/aioboto3 accept use_ssl
        if settings.S3_USE_SSL is not None:
            self.client_params["use_ssl"] = settings.S3_USE_SSL

    async def upload_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Upload raw bytes to S3 and return object key."""
        async with self.session.client("s3", **self.client_params) as client:
            kwargs = {"Bucket": self.bucket, "Key": key, "Body": data}
            if content_type:
                kwargs["ContentType"] = content_type
            await client.put_object(**kwargs)
        return key

    async def delete_object(self, key: str) -> bool:
        async with self.session.client("s3", **self.client_params) as client:
            await client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def generate_presigned_url(self, key: str, expires_in: int = 3600, method: str = "get_object") -> str:
        """Generate a presigned URL using synchronous boto3 (safe to call from async code)."""
        # boto3 client generation is synchronous; use same params but without aioboto3 session
        params = {k: v for k, v in self.client_params.items() if k != "use_ssl"}
        # boto3 expects endpoint_url/region_name/etc. Use same keys
        if "endpoint_url" in self.client_params:
            params["endpoint_url"] = self.client_params["endpoint_url"]

        client = boto3.client("s3", **params)
        try:
            url = client.generate_presigned_url(ClientMethod=method, Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in)
            return url
        except ClientError as e:
            raise
