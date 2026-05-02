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
- **Nix Flake**: Currently uses `nixos-25.11`.
- **Dependency Management**: We attempted to use `poetry2nix`, but encountered persistent platform-specific evaluation errors (related to `riscv64` and `tomli` attributes in Nixpkgs).
- **Direnv**: `.envrc` is configured to watch flake and lock files.
- **UV Transition**: Started moving towards `uv2nix`. The `pyproject.toml` currently uses the Poetry-specific `[tool.poetry]` table and needs to be converted to the standard `[project]` table (PEP 621) for `uv` compatibility.

## How to Run
Currently, the most reliable way to run the tool is via the Nix development shell:
```bash
nix develop
# If inside the shell and dependencies aren't built by Nix:
poetry install
python main.py --help
```

## Testing
9 unit tests are implemented and passing, covering Auth, Processor logic, Metadata parsing, and the Rate Limiter.
```bash
pytest
```

## Next Steps / Pending Tasks
1. **PEP 621 Conversion**: Update `pyproject.toml` to use standard metadata so `uv` can generate a lockfile.
2. **uv2nix Implementation**: Update `flake.nix` to use `pyproject.nix` and `uv2nix` for a more stable build than `poetry2nix`.
3. **EXIF Injection**: Complete the `MetadataFixer` implementation using a library like `piexif` or `exiftool`.
4. **Pipeline Refinement**: Fully transition `processor.py` into a generic `MigrationPipeline` that can be configured via a YAML file.
5. **New Modules**: Implement a `LocalSource` or `GmailSource` to demonstrate the flexibility of the new architecture.

Refer to `PLAN.md` for the original roadmap details.
