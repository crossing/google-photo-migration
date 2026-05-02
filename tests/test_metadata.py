import pytest
from src.metadata.fixer import MetadataFixer

def test_parse_sidecar_json():
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
    assert metadata['timestamp'] == "1609502400"
    assert metadata['geo']['latitude'] == 40.7128
    assert metadata['geo']['longitude'] == -74.006

def test_apply_metadata_placeholder():
    fixer = MetadataFixer()
    media_bytes = b"fake-media-bytes"
    metadata = {"title": "test"}
    
    # Currently returns bytes as-is
    result = fixer.apply_metadata(media_bytes, metadata)
    assert result == media_bytes
