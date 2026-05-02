# AGENTS.md - Google Photo Migration

## Project Overview

A Python tool to migrate Google Photos from Takeout ZIPs stored in Google Drive to Google Photos. Uses Poetry for dependency management, Click for CLI, SQLite for state tracking, and Google APIs for Drive/Photos integration.

## Build/Lint/Test Commands

This project uses **poetry2nix** in a Nix shell (NixOS-compatible). Native `poetry` commands will not work.

### Nix Shell
```bash
# Enter development environment (poetry2nix provides Python with deps)
nix-shell

# Or with direnv (auto-activates when entering directory)
direnv allow
```

### Running the Application
```bash
# Inside nix-shell
python main.py

# With specific options
python main.py --folder "Takeout" --skip-indexing
```

### Testing
- **No test suite exists** - Add tests before making significant changes
- Run tests with: `pytest` (inside nix-shell after adding pytest as dependency)
- Run single test: `pytest tests/test_file.py::test_name`

### Linting/Formatting
```bash
# Format code (if black is added)
black src/ main.py

# Run linter (if ruff is added)
ruff check src/ main.py

# Type checking (if mypy is added)
mypy src/ main.py
```

### Dependency Management (pyproject.toml + poetry2nix)
```bash
# Edit pyproject.toml manually to add dependencies
# poetry2nix automatically installs deps from pyproject.toml on nix-shell entry

# To update the lock file (if needed)
poetry2nix --input pyproject.toml

# Note: poetry2nix is read-only for dependency management
# Do not use 'poetry add' - edit pyproject.toml directly
```

## Code Style Guidelines

### Python Version
- Target Python 3.11+

### Imports
- Use absolute imports within the package: `from src.module import Class`
- Group by: stdlib → third-party → local (recommended)
- Standard library imports first, then third-party, then relative imports

### Naming Conventions
```python
# Classes: PascalCase
class MigrationProcessor
class PhotosManager
class DriveManager

# Functions and variables: snake_case
def get_credentials(token_path, client_secrets_path)
def index_destination_library(self)
upload_token = ...
file_size = ...

# Constants: SCREAMING_SNAKE_CASE
SCOPES = [...]
```

### Type Hints
- Add type hints for function parameters and return values where helpful
- Not strictly enforced but appreciated for complex functions
```python
def get_file_size(self, file_id: str) -> int:
    ...
```

### Docstrings
- Use docstrings for public methods and classes
- Keep concise, focus on what the method does, not how
```python
def list_library_items(self, page_size=100):
    """Yields all media items in the library."""
    ...
```

### Error Handling
- Use basic exception handling for expected failures
- Print errors with context for user-facing operations
```python
try:
    upload_token = self.photos_mgr.upload_media_item(...)
except Exception as e:
    print(f"Error processing {file_path}: {e}")
```

### File Structure
```
src/
    auth.py           # OAuth authentication
    processor.py      # Main migration logic
    drive_manager.py  # Google Drive operations
    photos_manager.py # Google Photos operations
    state_db.py       # SQLite state tracking
main.py               # CLI entry point with Click
```

### Database (SQLite)
- Use parameterized queries to prevent SQL injection
- Always use context manager for connections
```python
with sqlite3.connect(self.db_path) as conn:
    conn.execute('SELECT ...', (param1, param2))
```

### CLI (Click)
- Use `@click.option()` for named parameters
- Provide sensible defaults
- Use `click.echo()` for output, not `print()`

### Dependencies
Key dependencies (see pyproject.toml):
- `google-api-python-client` - Google API bindings
- `google-auth-oauthlib` - OAuth flow
- `click` - CLI framework
- `remotezip` - Random access ZIP handling
- `requests` - HTTP client

## Development Workflow

1. Make changes to source files in `src/`
2. Test with `python main.py [options]` (inside nix-shell)
3. Add type hints and docstrings for non-obvious logic
4. Commit changes (if requested by user)

## Environment Setup

The project uses Nix for reproducible environments (see `shell.nix`):
```bash
# Enter development environment
nix-shell

# Or with direnv (auto-activates when entering directory)
direnv allow
```

Required files for OAuth:
- `client_secrets.json` - Google Cloud OAuth credentials
- `token.json` - Generated after first authentication run
