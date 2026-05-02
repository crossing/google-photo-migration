from typing import Any
from unittest.mock import MagicMock, patch

from src.core.interfaces import Sink, Source, StateStore
from src.processor import MigrationProcessor


def test_migration_processor_init() -> None:
    source = MagicMock(spec=Source)
    sink = MagicMock(spec=Sink)
    state = MagicMock(spec=StateStore)

    processor = MigrationProcessor(source, sink, state)
    assert processor.source == source
    assert processor.sink == sink
    assert processor.state == state


@patch('src.processor.RemoteZip')
def test_process_zip_file_already_indexed(_mock_remote_zip: Any) -> None:
    source = MagicMock(spec=Source)
    sink = MagicMock(spec=Sink)
    state = MagicMock(spec=StateStore)

    # In the refactored logic, it checks get_pending_items
    state.get_pending_items.return_value = []
    source.get_file_size.return_value = 1000

    processor = MigrationProcessor(source, sink, state)
    processor.process_zip_file("zip-123", "test.zip")

    # Should check for pending items
    state.get_pending_items.assert_called_once_with("zip-123")
