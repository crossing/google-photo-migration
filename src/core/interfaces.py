from abc import ABC, abstractmethod
from typing import Any, BinaryIO


class Source(ABC):
    @abstractmethod
    def list_folders(self) -> list[dict[str, Any]]:
        """List available folders/containers in the source."""
        pass

    @abstractmethod
    def list_items(self, folder_id: str) -> list[dict[str, Any]]:
        """List items in a specific folder."""
        pass

    @abstractmethod
    def get_item_stream(
        self,
        item_id: str,
        start: int | None = None,
        end: int | None = None
    ) -> bytes:
        """Get a stream for a specific item, optionally with a byte range."""
        pass

    @abstractmethod
    def get_file_size(self, file_id: str) -> int:
        """Get the total size of a file."""
        pass


class Sink(ABC):
    @abstractmethod
    def upload_item(self, filename: str, content: BinaryIO) -> str:
        """Upload an item and return an upload token."""
        pass

    @abstractmethod
    def batch_create(self, upload_tokens: list[str]) -> dict[str, Any]:
        """Finalize a batch of uploads."""
        pass


class StateStore(ABC):
    @abstractmethod
    def add_items(self, items: list[tuple[str, str, str]]) -> None:
        """Add media items to the store for tracking."""
        pass

    @abstractmethod
    def get_pending_items(self, container_id: str) -> list[tuple[int, str]]:
        """Get items that haven't been successfully processed yet."""
        pass

    @abstractmethod
    def mark_completed(self, item_id: int, upload_token: str) -> None:
        """Mark an item as successfully processed."""
        pass

    @abstractmethod
    def mark_failed(self, item_id: int, error_message: str) -> None:
        """Mark an item as failed."""
        pass

    @abstractmethod
    def get_uploaded_tokens(self) -> list[str]:
        """Get tokens for items that are uploaded but not yet completed."""
        pass
