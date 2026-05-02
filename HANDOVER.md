# Handover Document - Google Data Migration Suite

## Current Status
The codebase has been refactored from a single-purpose script into a modular, interface-driven suite designed for large-scale Google data migrations.

### Architectural Changes
- **Modular Core**: Created `src/core/interfaces.py` defining `Source`, `Sink`, and `StateStore` ABCs.
- **Service Decoupling**:
    - `src/sources/google_drive.py`: Implements `Source` for reading ZIPs from Drive.
    - `src/sinks/google_photos.py`: Implements `Sink` for uploading to Photos.
    - `src/state/sqlite_state.py`: Implements `StateStore` using SQLite.
- **Multi-Account Support**: `src/auth/google_auth.py` and `src/cli.py` now support independent credentials for source and sink accounts.
- **Resilience**: Implemented `src/core/rate_limiter.py` providing a `@rate_limit_retry` decorator with exponential backoff.
- **Metadata Skeleton**: Added `src/metadata/fixer.py` for future EXIF re-injection logic.

### Environment & Nix
- **Nix Flake**: Updated to `nixos-24.11`.
- **Dependency Management**: Transitioned from `poetry2nix` to `uv2nix`.
- **PEP 621**: `pyproject.toml` has been converted to the standard `[project]` table.
- **Direnv**: `.envrc` is configured to watch flake and lock files.

## How to Run
```bash
nix develop
# Your environment is now ready with all dependencies installed via Nix
gphoto-migrate --help
```

## Testing
10 unit tests are implemented and passing.
```bash
pytest
```

## Next Steps / Pending Tasks
1. [DONE] **PEP 621 Conversion**: Update `pyproject.toml` to use standard metadata so `uv` can generate a lockfile.
2. [DONE] **uv2nix Implementation**: Update `flake.nix` to use `pyproject.nix` and `uv2nix`.
3. **EXIF Injection**: Complete the `MetadataFixer` implementation using a library like `piexif` or `exiftool`.
4. **Pipeline Refinement**: Fully transition `processor.py` into a generic `MigrationPipeline` that can be configured via a YAML file.
5. **New Modules**: Implement a `LocalSource` or `GmailSource` to demonstrate the flexibility of the new architecture.

Refer to `PLAN.md` for the original roadmap details.
