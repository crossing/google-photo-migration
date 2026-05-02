import pytest
from src.auth.google_auth import get_credentials
from src.sources.google_drive import DriveManager
from src.sinks.google_photos import PhotosManager
from src.processor import MigrationProcessor
from src.state.sqlite_state import MigrationStateDB

def test_imports():
    """Verify that all core components can be imported from their new locations."""
    assert DriveManager is not None
    assert PhotosManager is not None
    assert MigrationProcessor is not None
    assert MigrationStateDB is not None
