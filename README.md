# Google Photos Migration Tool

Migrate Google Photos from Takeout ZIPs in Google Drive.

## Features
- **Direct Drive to Photos**: Downloads ZIPs from Google Drive, extracts media in memory, and uploads to Google Photos.
- **Metadata Rehydration**: Automatically parses Google Takeout sidecar JSON files and re-injects EXIF data (Date Taken, GPS, Description) into media files before upload using `exiftool`.
- **Resilient**: Tracks progress in a SQLite database to resume interrupted migrations.
- **Cross-Platform State**: Defaults to standard XDG data directories (Linux) or equivalents (macOS).

## Prerequisites
- **exiftool**: Required for metadata rehydration. Included automatically if using the Nix package.

## Development

This project uses [Nix](https://nixos.org/) with [uv2nix](https://github.com/pyproject-nix/uv2nix) for development.

```bash
nix develop
# Your environment is now ready with all dependencies including exiftool
gphoto-migrate --help
```

## Usage

```bash
gphoto-migrate --source-secrets client_secrets.json --sink-secrets client_secrets.json --folder "Takeout"
```

The migration state is stored in a SQLite database. By default, it is located in:
- Linux: `~/.local/share/google-photo-migration/migration_state.db`
- macOS: `~/Library/Application Support/google-photo-migration/migration_state.db`

You can override this with `--db-path`.

## Testing

Inside the `nix develop` shell:
```bash
pytest
```
