import logging
import click
import os
from src.auth.google_auth import get_credentials, DRIVE_SCOPES, PHOTOS_SCOPES
from src.sources.google_drive import DriveManager
from src.sinks.google_photos import PhotosManager
from src.processor import MigrationProcessor
from src.state.sqlite_state import MigrationStateDB

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=click.get_text_stream('stdout')
)


@click.command()
@click.option('--source-secrets', default='client_secrets.json', help='Path to source client_secrets.json')
@click.option('--sink-secrets', default='client_secrets.json', help='Path to sink client_secrets.json')
@click.option('--source-token', default='token_drive.json', help='Path to store source OAuth token')
@click.option('--sink-token', default='token_photos.json', help='Path to store sink OAuth token')
@click.option('--db-path', default='migration_state.db', help='Path to SQLite state database')
@click.option('--folder', default=None, help='Name of the folder in Google Drive containing Takeout ZIPs')
def main(source_secrets, sink_secrets, source_token, sink_token, db_path, folder):
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

    drive_mgr = DriveManager(source_creds)
    photos_mgr = PhotosManager(sink_creds)
    state_db = MigrationStateDB(db_path)
    processor = MigrationProcessor(drive_mgr, photos_mgr, state_db)

    click.echo("--- Google Photos Migration Tool ---")

    selected_folder = _select_folder(drive_mgr, folder)
    if not selected_folder:
        return

    zips = drive_mgr.list_zips_in_folder(selected_folder['id'])
    if not zips:
        click.echo("No ZIP files found in the selected folder.")
        return

    click.echo(f"Found {len(zips)} ZIP files.")
    for zip_file in zips:
        processor.process_zip_file(zip_file['id'], zip_file['name'])

    click.echo("Migration complete!")


def _select_folder(drive_mgr, folder_name):
    if folder_name:
        click.echo(f"Searching for folder: {folder_name}...")
        folders = drive_mgr.list_folders()
        for f in folders:
            if f['name'].lower() == folder_name.lower():
                return f
        click.echo(f"Error: Folder '{folder_name}' not found.")
        return None

    click.echo("Scanning for folders in Google Drive...")
    folders = drive_mgr.list_folders()
    if not folders:
        click.echo("No folders found in Google Drive.")
        return None

    for idx, f in enumerate(folders):
        click.echo(f"{idx + 1}. {f['name']} ({f['id']})")

    choice = click.prompt("Select the folder containing Takeout ZIP files", type=int)
    return folders[choice - 1]


if __name__ == '__main__':
    main()
