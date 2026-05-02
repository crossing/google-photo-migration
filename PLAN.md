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
7. Add logic to re-inject EXIF/metadata into files during the migration process.
8. Enforce a strict commit strategy: Each commit must be modular, self-contained, and accompanied by sufficient test coverage.

## Proposed Solution & Implementation Steps

### Phase 1: Repository Setup & Structural Refactoring
- [x] 
 Initialize the repository on GitHub using the `gh repo create` command.
- [x] 
 Move `main.py` logic into `src/cli.py` and configure `pyproject.toml` to use `src.cli:main` as the entrypoint.
- [x] 
 Create `src/core/`, `src/sources/`, `src/sinks/`, `src/state/`, `src/metadata/`, and `src/auth/` directories.
- *Commit Rule*: Move files, update pyproject, and verify the CLI runs via poetry/nix. Add basic `pytest` setup.

### Phase 2: Multi-Account Authentication
- [x] 
 Refactor `src/auth.py` to allow instantiating multiple credential objects concurrently.
- [x] 
 Update CLI arguments to accept distinct `source-client-secrets` and `sink-client-secrets` (or multiple profiles/tokens).
- *Commit Rule*: Implement the new auth logic, write unit tests for the auth module, and commit.

### Phase 3: Interface Abstraction (Sources, Sinks, State)
- [x] 
 Define `Source` ABC with methods like `list_items()`, `get_stream()`.
- [x] 
 Define `Sink` ABC with methods like `upload_item()`, `batch_commit()`.
- [x] 
 Define `StateStore` ABC for tracking migration progress.
- [x] 
 Refactor `processor.py` (which becomes `MigrationPipeline`) to accept any `Source`, `Sink`, and `StateStore`.
- *Commit Rule*: Implement the ABCs and refactored pipeline with unit tests using mock sources/sinks.

### Phase 4: Metadata Re-injection
- [x] 
 Implement a `MetadataFixer` class in `src/metadata/` that can parse sidecar JSON files (common in Google Takeout) or extract existing EXIF data.
- [x] 
 Update the `MigrationPipeline` to optionally pass the stream through the `MetadataFixer` before sending it to the `Sink`.
- *Commit Rule*: Implement metadata logic, add tests with sample media/JSON, and commit.

### Phase 5: Resilience and Rate Limiting
- [x] 
 Implement a generic `RateLimiter` decorator or utility using exponential backoff.
- [x] 
 Wrap API calls (like `PhotosManager`) with the `RateLimiter`.
- *Commit Rule*: Implement RateLimiter, write tests verifying backoff behavior, and commit.

### Phase 6: Documentation
- [x] 
 Save this plan as `PLAN.md` in the repository root for future tracking.
- [x] 
 Expand `README.md` to describe the new architecture, how to run tests, and how to execute cross-account migrations.

## Alternatives Considered
- **Keeping the script-like structure:** Rejected because adding new sources/sinks would lead to a monolithic and unmaintainable `main.py` and `processor.py`.
- **Global Auth Context:** Rejected because we need to explicitly support cross-account operations (e.g., Source Account A -> Target Account B), requiring isolated `Credentials` instances.

## Verification & Testing Guidelines
- **Self-Contained Commits:** Every feature branch or commit must be fully functional and include its own unit tests. No "tests coming later" commits.
- **Coverage:** Ensure high test coverage (aim for >80% coverage) using `pytest-cov`.
- **E2E Parity:** Run the refactored CLI with the existing `Drive -> Photos` migration flow on a test folder to ensure parity before concluding the refactoring.