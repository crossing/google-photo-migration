import pytest
from unittest.mock import MagicMock, patch
from src.processor import MigrationProcessor
from src.core.interfaces import Source, Sink, StateStore

def test_migration_processor_init():
    source = MagicMock(spec=Source)
    sink = MagicMock(spec=Sink)
    state = MagicMock(spec=StateStore)
    
    processor = MigrationProcessor(source, sink, state)
    assert processor.source == source
    assert processor.sink == sink
    assert processor.state == state

@patch('src.processor.RemoteZip')
def test_process_zip_file_already_indexed(mock_remote_zip):
    source = MagicMock(spec=Source)
    sink = MagicMock(spec=Sink)
    state = MagicMock(spec=StateStore)
    
    state.is_indexed.return_value = True
    state.get_pending_items.return_value = []
    source.get_item_size.return_value = 1000
    
    processor = MigrationProcessor(source, sink, state)
    processor.process_zip_file("zip-123", "test.zip")
    
    state.is_indexed.assert_called_once_with("zip-123")
    # Should still check for pending items and recover tokens
    state.get_pending_items.assert_called_once_with("zip-123")
