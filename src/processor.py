import io
import logging
from typing import Any

from remotezip import RemoteZip

from src.core.interfaces import Sink, Source, StateStore

logger = logging.getLogger(__name__)


class DriveZipFetcher:
    def __init__(
        self,
        url: str,
        session: Any | None = None,
        zip_id: str | None = None,
        source: Source | None = None,
        file_size: int | None = None,
    ):
        self._url = url
        self._zip_id = zip_id
        self._source = source
        self._file_size = file_size or 0
        self._session = session  # Store it to avoid unused argument warning

    def get_file_size(self) -> int:
        return self._file_size

    def fetch(self, start: int, end: int | None = None, stream: bool = False) -> bytes:
        if self._source is None or self._zip_id is None:
            raise ValueError("Source and zip_id must be provided to fetch data.")

        if end is None:
            end = self._file_size - 1
        logger.debug(
            "  [FETCH] bytes=%s-%s (%s total) stream=%s",
            start, end, self._file_size, stream
        )
        data = self._source.get_item_stream(self._zip_id, start, end)
        logger.debug("  [FETCH] Got %s bytes", len(data))
        return data


class MigrationProcessor:
    def __init__(self, source: Source, sink: Sink, state: StateStore):
        self.source = source
        self.sink = sink
        self.state = state

    def process_zip_file(self, zip_id: str, zip_filename: str) -> None:
        """Process a single ZIP file from Drive and upload its contents to Photos."""
        logger.info("Processing ZIP: %s", zip_filename)

        file_size = self.source.get_file_size(zip_id)
        logger.info("  ZIP file size: %s bytes", file_size)

        def fetcher_factory(
            url: str, session: Any | None = None, **_kwargs: Any
        ) -> DriveZipFetcher:
            return DriveZipFetcher(
                url, session, zip_id=zip_id, source=self.source, file_size=file_size
            )

        with RemoteZip(
            zip_id,
            fetcher=fetcher_factory,  # pyright: ignore[reportArgumentType]
            initial_buffer_size=64 * 1024 * 1024
        ) as rzip:
            all_files = rzip.namelist()
            media_files = [
                f
                for f in all_files
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".mov"))
            ]

            logger.info("  Found %s media files in ZIP.", len(media_files))

            # Store pending items in DB if not already there
            current_pending = self.state.get_pending_items(zip_id)
            if not current_pending and media_files:
                items_to_add = [(zip_id, zip_filename, f) for f in media_files]
                self.state.add_items(items_to_add)
                current_pending = self.state.get_pending_items(zip_id)

            logger.info("  %s items pending upload.", len(current_pending))

            # Process in batches
            batch_size = 10
            upload_tokens: list[str] = []
            current_batch_ids: list[int] = []

            for item_id, file_path in current_pending:
                try:
                    logger.info("    Uploading %s...", file_path)
                    with rzip.open(file_path) as f:
                        # RemoteZip's open returns a file-like object
                        content = io.BytesIO(f.read())
                        token = self.sink.upload_item(file_path, content)
                        upload_tokens.append(token)
                        current_batch_ids.append(item_id)

                    if len(upload_tokens) >= batch_size:
                        self._batch_create_and_update(upload_tokens, current_batch_ids)
                        upload_tokens = []
                        current_batch_ids = []

                except Exception as e:
                    logger.error("    Error uploading %s: %s", file_path, e)
                    self.state.mark_failed(item_id, str(e))

            # Final batch
            if upload_tokens:
                self._batch_create_and_update(upload_tokens, current_batch_ids)

    def _batch_create_and_update(self, tokens: list[str], item_ids: list[int]) -> None:
        try:
            results = self.sink.batch_create(tokens)
            media_results = results.get("newMediaItemResults", [])

            for i, result in enumerate(media_results):
                status = result.get("status", {})
                if status.get("message") == "Success":
                    self.state.mark_completed(item_ids[i], tokens[i])
                else:
                    self.state.mark_failed(item_ids[i], status.get("message", "Unknown error"))
            logger.info("    Created %s items in Sink.", len(tokens))
        except Exception as e:
            logger.error("  Error creating items: %s", e)
            for item_id in item_ids:
                self.state.mark_failed(item_id, f"Batch creation failed: {e}")

    def recover_pending_uploads(self) -> None:
        """Attempts to finalize items that were uploaded but not committed."""
        tokens = self.state.get_uploaded_tokens()
        if tokens:
            logger.info("Recovering %s pending upload tokens...", len(tokens))
            # Note: This is simplified; we'd need item_ids to mark them correctly
            # For now, we just try to batch create them.
            try:
                self.sink.batch_create(tokens)
            except Exception as e:
                logger.error("Failed to recover uploads: %s", e)
