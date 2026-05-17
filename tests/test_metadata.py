from unittest.mock import MagicMock, patch

from src.metadata.fixer import MetadataFixer


def test_parse_sidecar_json() -> None:
    fixer = MetadataFixer()
    json_data = b'''
    {
      "title": "IMG_20210101_120000.jpg",
      "description": "New Year 2021",
      "photoTakenTime": {
        "timestamp": "1609502400",
        "formatted": "Jan 1, 2021, 12:00:00 PM UTC"
      },
      "geoData": {
        "latitude": 40.7128,
        "longitude": -74.006,
        "altitude": 0.0,
        "latitudeSpan": 0.0,
        "longitudeSpan": 0.0
      }
    }
    '''
    metadata = fixer.parse_sidecar_json(json_data)

    assert metadata['title'] == "IMG_20210101_120000.jpg"
    assert metadata['description'] == "New Year 2021"
    # Access nested field correctly
    assert metadata['photoTakenTime']['timestamp'] == "1609502400"


def test_apply_metadata_best_effort_on_error() -> None:
    fixer = MetadataFixer()
    media_bytes = b"fake-media-bytes"
    metadata = {"description": "test"}

    # Even if exiftool fails (e.g. not installed), it should return original bytes
    with patch("src.metadata.fixer.ExifToolHelper", side_effect=RuntimeError("ExifTool not found")):
        result = fixer.apply_metadata(media_bytes, metadata)
        assert result == media_bytes


@patch("src.metadata.fixer.ExifToolHelper")
@patch("builtins.open")
@patch("os.unlink")
@patch("os.path.exists")
def test_apply_metadata_calls_exiftool(
    mock_exists: MagicMock,
    mock_unlink: MagicMock,
    mock_open: MagicMock,
    mock_et_class: MagicMock
) -> None:
    fixer = MetadataFixer()
    media_bytes = b"original-bytes"
    metadata = {
        "photoTakenTime": {"timestamp": "1609502400"},
        "geoData": {"latitude": 40.7128, "longitude": -74.006, "altitude": 10.0},
        "description": "test description"
    }

    # Setup mocks
    mock_et = mock_et_class.return_value.__enter__.return_value
    mock_exists.return_value = True
    
    # Mock open to return "modified-bytes" when reading back
    # Note: open is called for writing original bytes too, so we need to handle that if we want to be precise.
    # But for a simple test, we can just check if it returns what we expect.
    mock_open.return_value.__enter__.return_value.read.return_value = b"modified-bytes"

    result = fixer.apply_metadata(media_bytes, metadata)

    assert result == b"modified-bytes"
    mock_et.set_tags.assert_called_once()
    
    _, kwargs = mock_et.set_tags.call_args
    tags = kwargs["tags"]
    assert tags["DateTimeOriginal"] == "2021:01:01 12:00:00"  # UTC 1609502400
    assert tags["GPSLatitude"] == 40.7128
    assert tags["GPSLongitude"] == -74.006
    assert tags["GPSAltitude"] == 10.0
    assert tags["Description"] == "test description"
