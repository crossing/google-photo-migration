import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from typing import Any

from exiftool import ExifToolHelper

logger = logging.getLogger(__name__)


class MetadataFixer:
    """Handles parsing and re-injecting metadata from sidecar JSON files."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or os.environ.get("GPHOTO_EXIFTOOL_BIN", "exiftool")

    def parse_sidecar_json(self, json_bytes: bytes) -> dict[str, Any]:
        """Parse Google Takeout sidecar JSON metadata."""
        try:
            return dict(json.loads(json_bytes))
        except Exception as e:
            logger.error("Error parsing sidecar JSON: %s", e)
            return {}

    def apply_metadata(self, media_bytes: bytes, metadata: dict[str, Any]) -> bytes:
        """
        Re-inject EXIF data into media bytes using exiftool.
        Best-effort: returns original bytes on failure.
        """
        if not metadata:
            return media_bytes

        tmp_path = None
        try:
            # Create a temporary file to work with exiftool
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(media_bytes)
                tmp_path = tmp.name

            tags: dict[str, Any] = {}

            # 1. Photo Taken Time
            if "photoTakenTime" in metadata:
                try:
                    ts = int(metadata["photoTakenTime"]["timestamp"])
                    dt = datetime.fromtimestamp(ts, tz=UTC)
                    # Exif format: YYYY:MM:DD HH:MM:SS
                    formatted_date = dt.strftime("%Y:%m:%d %H:%M:%S")
                    tags["DateTimeOriginal"] = formatted_date
                    tags["CreateDate"] = formatted_date
                    tags["ModifyDate"] = formatted_date
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning("Could not parse photoTakenTime: %s", e)

            # 2. Geo Data
            if "geoData" in metadata:
                try:
                    lat = metadata["geoData"].get("latitude")
                    lon = metadata["geoData"].get("longitude")
                    alt = metadata["geoData"].get("altitude")

                    # Only add if we have at least lat/lon and they aren't 0.0 (often default)
                    # Note: 0.0, 0.0 is a valid coordinate but often means "missing" in Takeout
                    if lat != 0.0 or lon != 0.0:
                        tags["GPSLatitude"] = lat
                        tags["GPSLongitude"] = lon
                        if alt is not None:
                            tags["GPSAltitude"] = alt
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning("Could not parse geoData: %s", e)

            # 3. Description
            if metadata.get("description"):
                tags["Description"] = metadata["description"]
                tags["UserComment"] = metadata["description"]

            if tags:
                with ExifToolHelper(executable=self.executable) as et:
                    et.set_tags([tmp_path], tags=tags, params=["-overwrite_original", "-q"])

            with open(tmp_path, "rb") as f:
                new_bytes = f.read()

            return new_bytes

        except Exception as e:
            logger.warning("Failed to apply metadata: %s. Continuing with original bytes.", e)
            return media_bytes
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.debug("Failed to delete temp file %s: %s", tmp_path, e)
