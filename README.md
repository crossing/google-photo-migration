# Google Photos Migration Tool

Migrate Google Photos from Takeout ZIPs in Google Drive.

## Development

This project uses [Nix](https://nixos.org/) with [uv2nix](https://github.com/pyproject-nix/uv2nix) for development.

```bash
nix develop
# Your environment is now ready with all dependencies
gphoto-migrate --help
```

## Testing

Inside the `nix develop` shell:
```bash
pytest
```
