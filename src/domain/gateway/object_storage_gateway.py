from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class IObjectStorageGateway(ABC):
    """Gateway abstraction for object storage providers."""

    @abstractmethod
    def upload(self, key: str, fileobj: BinaryIO, content_type: str) -> str:
        """Upload a stream to storage and return the public or internal URL/key."""

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download an object identified by the key."""
