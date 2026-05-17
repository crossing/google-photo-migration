# Google Drive to Google Drive Migration Plan

## 1. Goal and Scope
Extend the existing migration framework to support Google Drive to Google Drive migration, while keeping the existing architecture (resumable, metadata tracking). The application and repository will be generalized and renamed to reflect this broader scope.

## 2. Architecture Extensions
*   **Generalize App Name**: Rename the repository and application from `google-photo-migration` to `cloud-media-migrator` (or similar).
*   **Interfaces**: 
    *   The existing `Source`, `Sink`, and `StateStore` are solid and reusable.
    *   We will add a new `DriveSink` (implementing `Sink`) under `src/sinks/google_drive.py`.
*   **Processor**: 
    *   Create a `DriveMigrationProcessor` that handles regular file/folder recursive copying instead of ZIP extraction.
    *   It will interface with `DriveManager` (as Source) and `DriveSink` (as Sink).
*   **CLI Structure**:
    *   Change `cli.py` to use `click.Group` to support multiple commands: `migrator photos` (existing flow) and `migrator drive` (new flow).

## 3. Data Transfer Strategy (Minimizing Download/Upload)
To use the API whenever possible and keep I/O to a minimum:
*   **Drive API `copy` (Fast Path)**: The Google Drive API allows native server-side copying via `files().copy()`. This requires the authenticated Sink account to have read access to the Source file (e.g., if the user is migrating within the same account, or if the folders are shared across the two accounts). The `DriveMigrationProcessor` will detect this and attempt a native `copy` first.
*   **Streamed Upload (Fallback Path)**: If the native copy fails (due to lack of cross-account sharing permissions), the processor will stream the data directly from `Source.get_item_stream()` into `Sink.upload_item()` in chunks, strictly avoiding saving full files to the local disk.

## 4. Source and Destination Folders
*   Update `cli.py` in the new `drive` command to accept `--source-folder` and `--dest-folder`.
*   If not provided, the CLI will use an interactive prompt (similar to the existing `_select_folder`) for both the Source account and the Destination account, presenting a navigable list of available folders.

## 5. Diff Reports / Dry Run
*   Add a `--diff` or `--dry-run` flag to the `drive` command.
*   **Implementation**:
    *   Recursively fetch all items from the `--source-folder` (Source state).
    *   Compare against the local `StateStore` database to identify:
        *   **New**: Exists in Source, missing in local tracking state.
        *   **Updated**: Exists in local state but file size or modified time differs.
        *   **Removed**: Exists in local state but no longer in Source.
    *   Output a cleanly formatted diff report to the terminal instead of executing the migration.

## 6. Execution Steps
1.  **Refactor & Rename**: Rename project files, update `pyproject.toml`, and adjust imports to the new generalized naming convention.
2.  **Implement `DriveSink`**: Build upload and API `copy` functionality in a new sink for Google Drive.
3.  **Implement `DriveMigrationProcessor`**: Build the orchestrator that attempts the native API copy and falls back to memory-streamed transfers.
4.  **Implement Diff Engine**: Add logic to compare Source files against `StateStore` and output the diff report.
5.  **Update CLI**: Implement the `click.Group` with `drive` and `photos` subcommands, including all necessary options (`--source-folder`, `--dest-folder`, `--diff`).
