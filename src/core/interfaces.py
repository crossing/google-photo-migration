from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator, BinaryIO

class Source(ABC):
    @abstractmethod
    def list_folders(self) -> List[Dict[str, Any]]:
        """List available folders/containers in the source."""
        pass

    @abstractmethod
    def list_items(self, folder_id: str) -> List[Dict[str, Any]]:
        """List items in a specific folder."""
        pass

    @abstractmethod
    def get_item_stream(self, item_id: str, start_byte: int, end_byte: int) -> bytes:
        """Get a byte range of an item."""
        pass

    @abstractmethod
    def get_item_size(self, item_id: str) -> int:
        """Get the total size of an item in bytes."""
        pass

class Sink(ABC):
    @abstractmethod
    def upload_item(self, file_bytes: bytes, filename: str) -> str:
        """Upload raw bytes and return an upload token/id."""
        pass

    @abstractmethod
    def batch_create(self, upload_tokens: List[str]) -> Dict[str, Any]:
        """Finalize a batch of uploads."""
        pass

class StateStore(ABC):
    @abstractmethod
    def is_indexed(self, container_id: str) -> bool:
        """Check if a container (e.g. ZIP) has been indexed."""
        pass

    @abstractmethod
    def mark_indexed(self, container_id: str, container_name: str):
        """Mark a container as indexed."""
        pass

    @abstractmethod
    def add_items(self, items: List[tuple]):
        """Add media items to the store for tracking."""
        pass

    @abstractmethod
    def get_pending_items(self, container_id: str) -> List[tuple]:
        """Get items that haven't been successfully processed yet."""
        pass

    @abstractmethod
    def mark_uploaded(self, item_id: Any, upload_token: str):
        """Mark an item as uploaded to the sink."""
        pass

    @abstractmethod
    def mark_completed(self, upload_token: str):
        """Mark an item as fully created in the sink."""
        pass

    @abstractmethod
    def get_uploaded_tokens(self) -> List[str]:
        """Get tokens for items that are uploaded but not yet completed."""
        pass
