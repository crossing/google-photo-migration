import logging
import os

import click

from src.auth.google_auth import DRIVE_SCOPES, PHOTOS_SCOPES, get_credentials
from src.processor import MigrationProcessor
from src.sinks.google_photos import PhotosManager
from src.sources.google_drive import DriveManager
from src.state.sqlite_state import MigrationStateDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--source-secrets', default='client_secrets.json', help='Path to source secrets')
@click.option('--sink-secrets', default='client_secrets.json', help='Path to sink secrets')
@click.option('--source-token', default='token_drive.json', help='Path to source OAuth token')
@click.option('--sink-token', default='token_photos.json', help='Path to sink OAuth token')
@click.option('--db-path', default='migration_state.db', help='Path to SQLite state database')
@click.option('--folder', default=None, help='Folder in Google Drive containing Takeout ZIPs')
def main(
    source_secrets: str,
    sink_secrets: str,
    source_token: str,
    sink_token: str,
    db_path: str,
    folder: str | None
) -> None:
    """Google Photos Migration Tool (Takeout to Drive to Photos)"""
    if not os.path.exists(source_secrets):
        click.echo(f"Error: Source secrets {source_secrets} not found.")
        return

    if not os.path.exists(sink_secrets):
        click.echo(f"Error: Sink secrets {sink_secrets} not found.")
        return

    click.echo("Authenticating Source (Google Drive)...")
    source_creds = get_credentials(source_token, source_secrets, DRIVE_SCOPES)

    click.echo("Authenticating Sink (Google Photos)...")
    sink_creds = get_credentials(sink_token, sink_secrets, PHOTOS_SCOPES)

    source = DriveManager(source_creds)
    sink = PhotosManager(sink_creds)
    state = MigrationStateDB(db_path)

    processor = MigrationProcessor(source, sink, state)

    folder_id = _select_folder(source, folder)
    if not folder_id:
        click.echo("No folder selected. Exiting.")
        return

    zips = source.list_zips_in_folder(folder_id)
    if not zips:
        click.echo(f"No ZIP files found in folder {folder_id}.")
        return

    click.echo(f"Found {len(zips)} ZIP files. Starting migration...")
    for zip_info in zips:
        processor.process_zip_file(zip_info['id'], zip_info['name'])

    click.echo("Migration complete!")


def _select_folder(source: DriveManager, folder_name: str | None) -> str | None:
    if folder_name:
        folder_id = source.get_folder_id_by_name(folder_name)
        if folder_id:
            return folder_id
        click.echo(f"Folder '{folder_name}' not found.")

    folders = source.list_folders()
    if not folders:
        click.echo("No folders found in Google Drive.")
        return None

    click.echo("\nAvailable folders:")
    for i, f in enumerate(folders):
        click.echo(f"{i}: {f['name']} ({f['id']})")

    choice = click.prompt("\nSelect a folder index", type=int)
    if 0 <= choice < len(folders):
        return str(folders[choice]['id'])

    return None


if __name__ == "__main__":
    main()
