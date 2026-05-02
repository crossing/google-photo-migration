import io
import logging
import os
from remotezip import PartialBuffer, RemoteZip
from .drive_manager import DriveManager
from .photos_manager import PhotosManager
from .state_db import MigrationStateDB

logger = logging.getLogger(__name__)


class DriveZipFetcher:
    def __init__(self, url, session=None, zip_id=None, drive_mgr=None, file_size=None):
        self._url = url
        self._zip_id = zip_id
        self._drive_mgr = drive_mgr
        self._file_size = file_size
        self._support_suffix_range = True

    def get_file_size(self):
        return self._file_size

    @staticmethod
    def parse_range_header(content_range_header):
        range = content_range_header[6:].split("/")[0]
        if range.startswith("-"):
            return int(range), None
        range_min, range_max = range.split("-")
        return int(range_min), int(range_max) if range_max else None

    @staticmethod
    def build_range_header(range_min, range_max):
        if range_max is None:
            return "bytes=%s%s" % (range_min, '' if range_min < 0 else '-')
        return "bytes=%s-%s" % (range_min, range_max)

    def fetch(self, data_range, stream=False):
        start, end = data_range
        
        if start < 0 and end is None:
            size = self.get_file_size()
            start = max(0, size + start)
            end = size - 1

        if end is None:
            end = self._file_size - 1
        logger.debug("  [FETCH] bytes=%s-%s (%s total) stream=%s", start, end, self._file_size, stream)
        data = self._drive_mgr.get_file_bytes_range(self._zip_id, start, end)
        logger.debug("  [FETCH] Got %s bytes", len(data))
        
        return PartialBuffer(
            io.BytesIO(data),
            start,
            end - start + 1,
            stream
        )


class MigrationProcessor:
    def __init__(self, drive_mgr, photos_mgr, state_db):
        self.drive_mgr = drive_mgr
        self.photos_mgr = photos_mgr
        self.state_db = state_db

    def process_zip_file(self, zip_id, zip_filename):
        """Processes a single ZIP file from Drive using random access streaming."""
        logger.info("Processing ZIP: %s", zip_filename)

        already_indexed = self.state_db.is_zip_indexed(zip_id)
        if already_indexed:
            logger.info("  ZIP already indexed, skipping re-indexing.")

        self._recover_uploaded_tokens()

        file_size = self.drive_mgr.get_file_size(zip_id)
        logger.info("  ZIP file size: %s bytes", file_size)

        fetcher_factory = lambda url, session=None, file_size=file_size, **kwargs: \
            DriveZipFetcher(url, session, zip_id=zip_id, drive_mgr=self.drive_mgr, file_size=file_size)

        with RemoteZip(zip_id, fetcher=fetcher_factory, initial_buffer_size=64*1024*1024) as rzip:
            if not already_indexed:
                logger.info("  Indexing ZIP contents...")
                try:
                    infolist = rzip.infolist()
                except Exception as e:
                    logger.error("  ERROR in infolist: %s", e)
                    raise
                logger.info("  Found %s entries in ZIP", len(infolist))
                items_to_add = []
                for i, zip_info in enumerate(infolist):
                    if zip_info.is_dir():
                        continue
                    items_to_add.append((zip_id, zip_filename, zip_info.filename))
                    if (i + 1) % 100 == 0:
                        logger.info("    Indexed %s items...", i + 1)

                logger.info("  Inserting items into database...")
                self.state_db.add_media_items_batch(items_to_add)
                self.state_db.mark_zip_indexed(zip_id, zip_filename)
                logger.info("  ZIP indexed successfully.")

            pending_items = self.state_db.get_pending_items(zip_id)
            if not pending_items:
                logger.info("  All items already uploaded, skipping.")
                return

            logger.info("  %s items to upload...", len(pending_items))

            upload_tokens = []

            for item in pending_items:
                item_id, file_path = item[0], item[1]
                try:
                    file_bytes = rzip.read(file_path)
                    upload_token = self.photos_mgr.upload_media_item(
                        file_bytes, os.path.basename(file_path)
                    )
                    self.state_db.mark_uploaded(item_id, upload_token)
                    upload_tokens.append(upload_token)

                    if len(upload_tokens) >= 49:
                        self._batch_create(upload_tokens)
                        upload_tokens = []

                except Exception as e:
                    logger.error("  Error uploading %s: %s", file_path, e)

            if upload_tokens:
                self._batch_create(upload_tokens)

            stats = self.state_db.get_stats(zip_id)
            logger.info("  Done. Status: %s", stats)

    def _batch_create(self, upload_tokens):
        """Finalize batch of uploads in Google Photos."""
        try:
            self.photos_mgr.batch_create_media_items(upload_tokens)
            for token in upload_tokens:
                self.state_db.mark_created(token)
            logger.info("  Created %s items in Photos.", len(upload_tokens))
        except Exception as e:
            logger.error("  Error batch creating items: %s", e)
            raise

    def _recover_uploaded_tokens(self):
        """Recover any uploaded tokens that weren't batch-created."""
        uploaded_tokens = self.state_db.get_uploaded_tokens()
        if uploaded_tokens:
            logger.info("  Recovering %s uploaded tokens...", len(uploaded_tokens))

            import time
            batch = []
            for token in uploaded_tokens:
                batch.append(token)
                if len(batch) >= 49:
                    try:
                        self.photos_mgr.batch_create_media_items(batch)
                        for t in batch:
                            self.state_db.mark_created(t)
                        logger.info("    Created %s items in Photos.", len(batch))
                    except Exception as e:
                        if "429" in str(e) or "RATE_LIMIT" in str(e):
                            logger.info("    Rate limited, waiting 60s...")
                            time.sleep(60)
                            continue
                        raise
                    batch = []

            if batch:
                try:
                    self.photos_mgr.batch_create_media_items(batch)
                    for t in batch:
                        self.state_db.mark_created(t)
                    logger.info("    Created %s items in Photos.", len(batch))
                except Exception as e:
                    logger.error("  Error creating items: %s", e)