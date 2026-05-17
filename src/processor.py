import io
import logging
from typing import Any

import remotezip

from src.core.interfaces import Sink, Source, StateStore
from src.metadata.fixer import MetadataFixer

logger = logging.getLogger(__name__)


class MigrationProcessor:
    def __init__(self, source: Source, sink: Sink, state: StateStore):
        self.source = source
        self.sink = sink
        self.state = state
        self.fixer = MetadataFixer()

    def process_zip_file(self, zip_id: str, zip_filename: str) -> None:
        """Process a single ZIP file from Drive and upload its contents to Photos."""
        logger.info("Processing ZIP: %s", zip_filename)

        file_size = self.source.get_file_size(zip_id)
        logger.info("  ZIP file size: %s bytes", file_size)

        def fetch_logic(data_range: tuple[int, int | None], _stream: bool = False) -> Any:
            start, end = data_range
            if start < 0:
                start = file_size + start
            if end is None or end >= file_size:
                end = file_size - 1

            chunk_size = end - start + 1
            logger.info("  [FETCH] Requesting %s bytes (%s to %s)...", chunk_size, start, end)
            data = self.source.get_item_stream(zip_id, start, end)
            logger.info("  [FETCH] Received %s bytes", len(data))

            # Use remotezip's own PartialBuffer implementation for maximum compatibility
            # It expects (buffer, offset, size, stream)
            return remotezip.PartialBuffer(io.BytesIO(data), start, len(data), False)

        class CustomFetcher:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def fetch(self, data_range: Any, stream: bool = False) -> Any:
                return fetch_logic(data_range, stream)

        try:
            # Pass our CustomFetcher class to RemoteZip
            # We use a larger initial buffer for 39GB+ files to help with indexing
            with remotezip.RemoteZip(
                zip_id,
                fetcher=CustomFetcher,  # pyright: ignore[reportArgumentType]
                initial_buffer_size=10*1024*1024
            ) as rzip:
                all_files = rzip.namelist()
                logger.info("  Finished indexing. Total files in ZIP: %s", len(all_files))

                media_files = [
                    f
                    for f in all_files
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".mp4", ".mov"))
                ]

                logger.info("  Found %s media files in ZIP.", len(media_files))

                # Store pending items in DB if not already there
                current_pending = self.state.get_pending_items(zip_id)
                if not current_pending and media_files:
                    logger.info(
                        "  First time processing this ZIP, adding %s items to database...",
                        len(media_files)
                    )
                    items_to_add = [(zip_id, zip_filename, f) for f in media_files]
                    self.state.add_items(items_to_add)
                    current_pending = self.state.get_pending_items(zip_id)

                logger.info("  %s items pending upload.", len(current_pending))

                # Process in batches
                batch_size = 10
                upload_tokens: list[str] = []
                current_batch_ids: list[int] = []

                for i, (item_id, file_path) in enumerate(current_pending):
                    try:
                        logger.info(
                            "    [%s/%s] Extracting and uploading %s...",
                            i + 1, len(current_pending), file_path
                        )

                        # Try to find sidecar JSON for metadata rehydration
                        metadata = {}
                        sidecar_path = f"{file_path}.json"
                        if sidecar_path in all_files:
                            try:
                                with rzip.open(sidecar_path) as sf:
                                    metadata = self.fixer.parse_sidecar_json(sf.read())
                            except Exception as e:
                                logger.warning("    Failed to read sidecar %s: %s", sidecar_path, e)

                        with rzip.open(file_path) as f:
                            media_bytes = f.read()

                            if metadata:
                                logger.info("    Applying metadata to %s", file_path)
                                media_bytes = self.fixer.apply_metadata(media_bytes, metadata)

                            content = io.BytesIO(media_bytes)
                            token = self.sink.upload_item(file_path, content)
                            upload_tokens.append(token)
                            current_batch_ids.append(item_id)

                        if len(upload_tokens) >= batch_size:
                            self._batch_create_and_update(upload_tokens, current_batch_ids)
                            upload_tokens = []
                            current_batch_ids = []

                    except Exception as e:
                        import traceback
                        logger.error("    Error uploading %s: %s", file_path, e)
                        logger.error(traceback.format_exc())
                        self.state.mark_failed(item_id, str(e))

                # Final batch
                if upload_tokens:
                    self._batch_create_and_update(upload_tokens, current_batch_ids)

        except Exception as e:
            logger.error("  Failed to process ZIP %s: %s", zip_filename, e)
            import traceback
            logger.error(traceback.format_exc())

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
