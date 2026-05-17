# Google Data Migration Suite - Architecture & Refactoring Plan

## Background & Motivation
The current tool successfully performs Google Takeout to Google Photos migration directly from Google Drive. However, the codebase is monolithic and tightly coupled to specific sources (Drive) and sinks (Photos). To scale this into a generalized "Google Data Migration Suite" that can handle various sources (Local, S3, Dropbox) and sinks, and even cross-account migrations (e.g. Gmail to Gmail), we need to decouple the components, improve error handling, support multi-account credential management, and transition to a more modular architecture.

## Scope & Impact
1. Initialize a GitHub repository using the `gh` command.
2. Refactor the existing codebase without breaking current Takeout-to-Photos functionality.
3. Reorganize directory structure to standard Python package format.
4. Introduce abstract base classes (ABCs) for `Source`, `Sink`, and `StateStore`.
5. Update `Auth` mechanisms to support loading distinct credentials for Source and Sink (allowing cross-account migrations).
6. Implement generic Rate Limiting and improved error handling for API calls.
7. Add logic to actually re-inject EXIF/metadata into files during the migration process using `exiftool` (Linux/macOS only, dropping Windows support).
8. Store the application state (SQLite db) in standardized XDG data directories by default using `platformdirs`.
9. Enforce a strict commit strategy: Each commit must be modular, self-contained, and accompanied by sufficient test coverage.

## Proposed Solution & Implementation Steps

### Phase 1: Repository Setup & Structural Refactoring
- [x] Initialize the repository on GitHub using the `gh repo create` command.
- [x] Move `main.py` logic into `src/cli.py` and configure `pyproject.toml` to use `src.cli:main` as the entrypoint.
- [x] Create `src/core/`, `src/sources/`, `src/sinks/`, `src/state/`, `src/metadata/`, and `src/auth/` directories.
- *Commit Rule*: Move files, update pyproject, and verify the CLI runs via poetry/nix. Add basic `pytest` setup.

### Phase 2: Multi-Account Authentication
- [x] Refactor `src/auth.py` to allow instantiating multiple credential objects concurrently.
- [x] Update CLI arguments to accept distinct `source-client-secrets` and `sink-client-secrets` (or multiple profiles/tokens).
- *Commit Rule*: Implement the new auth logic, write unit tests for the auth module, and commit.

### Phase 3: Interface Abstraction (Sources, Sinks, State)
- [x] Define `Source` ABC with methods like `list_items()`, `get_stream()`.
- [x] Define `Sink` ABC with methods like `upload_item()`, `batch_commit()`.
- [x] Define `StateStore` ABC for tracking migration progress.
- [x] Refactor `processor.py` (which becomes `MigrationPipeline`) to accept any `Source`, `Sink`, and `StateStore`.
- *Commit Rule*: Implement the ABCs and refactored pipeline with unit tests using mock sources/sinks.

### Phase 4: Metadata Re-injection (Implementation)
- [x] Implement a `MetadataFixer` class in `src/metadata/` that can parse sidecar JSON files (common in Google Takeout) or extract existing EXIF data.
- [x] Add `exiftool` as a Nix and Python dependency (e.g., `PyExifTool`).
- [x] Implement `MetadataFixer.apply_metadata` to actually write EXIF data (photo taken time, GPS) into media bytes before uploading using `exiftool`.
- [x] Update the `MigrationProcessor` to match sidecar JSON files with media files and pass both to `MetadataFixer` before sending to the `Sink`.
- [x] Ensure metadata rehydration is **best-effort**. If the sidecar is missing, corrupted, or `exiftool` fails, record a warning in the logs and continue uploading the media file as-is without blocking progress.
- *Commit Rule*: Implement metadata logic, add tests with sample media/JSON, and commit.

### Phase 5: Resilience and Rate Limiting
- [x] Implement a generic `RateLimiter` decorator or utility using exponential backoff.
- [x] Wrap API calls (like `PhotosManager`) with the `RateLimiter`.
- *Commit Rule*: Implement RateLimiter, write tests verifying backoff behavior, and commit.

### Phase 6: XDG Directory & App State Management
- [x] Add `platformdirs` to `pyproject.toml` dependencies.
- [x] Update `src/cli.py` to use `platformdirs.user_data_dir("google-photo-migration")` for the default SQLite database path.
- [x] Retain `--db-path` CLI option to override this default.
- *Commit Rule*: Implement platformdirs integration, test DB location creation, and commit.

### Phase 7: Documentation
- [x] Save this plan as `PLAN.md` in the repository root for future tracking.
- [x] Expand `README.md` to describe the new architecture, how to run tests, and how to execute cross-account migrations.
- [x] Update `README.md` to document XDG directories and `exiftool` dependency.

## Alternatives Considered
- **Keeping the script-like structure:** Rejected because adding new sources/sinks would lead to a monolithic and unmaintainable `main.py` and `processor.py`.
- **Global Auth Context:** Rejected because we need to explicitly support cross-account operations (e.g., Source Account A -> Target Account B), requiring isolated `Credentials` instances.
- **Pure Python EXIF Libraries:** Rejected in favor of `exiftool` for better and comprehensive support across image and video formats, as `exiftool` is easily provided via Nix.
- **Custom XDG path logic:** Rejected in favor of `platformdirs` to maintain standard cross-platform consistency without reinventing the wheel.

## Verification & Testing Guidelines
- **Self-Contained Commits:** Every feature branch or commit must be fully functional and include its own unit tests. No "tests coming later" commits.
- **Coverage:** Ensure high test coverage (aim for >80% coverage) using `pytest-cov`.
- **E2E Parity:** Run the refactored CLI with the existing `Drive -> Photos` migration flow on a test folder to ensure parity before concluding the refactoring.