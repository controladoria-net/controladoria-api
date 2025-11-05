from __future__ import annotations

import io
from typing import BinaryIO, Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.domain.gateway.object_storage_gateway import IObjectStorageGateway


class S3ObjectStorageGateway(IObjectStorageGateway):
    """Object storage gateway backed by Amazon S3."""

    def __init__(
        self,
        region: str,
        bucket: str,
        max_upload_size_mb: int = 25,
        client: Optional[BaseClient] = None,
    ) -> None:
        self._bucket = bucket
        self._max_upload_bytes = max_upload_size_mb * 1024 * 1024
        self._client = client or boto3.client(
            "s3",
            region_name=region,
            config=Config(retries={"max_attempts": 5, "mode": "standard"}),
        )

    def upload(self, key: str, fileobj: BinaryIO, content_type: str) -> str:
        self._ensure_size_within_limits(fileobj)
        try:
            fileobj.seek(0)
            self._client.upload_fileobj(  # type: ignore[arg-type]
                Fileobj=fileobj,
                Bucket=self._bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type or "application/octet-stream"},
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao enviar arquivo para o S3: {exc}") from exc
        return key

    def download(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao baixar arquivo do S3: {exc}") from exc
        body = response.get("Body")
        if body is None:
            raise RuntimeError("Resposta do S3 não contém corpo do arquivo.")
        return body.read()

    def _ensure_size_within_limits(self, fileobj: BinaryIO) -> None:
        current_position = fileobj.tell()
        try:
            fileobj.seek(0, io.SEEK_END)
            size = fileobj.tell()
        finally:
            fileobj.seek(current_position)
        if size > self._max_upload_bytes:
            megabytes = self._max_upload_bytes // (1024 * 1024)
            raise ValueError(
                f"Arquivo excede o tamanho máximo permitido de {megabytes}MB."
            )
