import logging
import click
import os
from src.auth import get_credentials
from src.drive_manager import DriveManager
from src.photos_manager import PhotosManager
from src.processor import MigrationProcessor
from src.state_db import MigrationStateDB

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=click.get_text_stream('stdout')
)


@click.command()
@click.option('--client-secrets', default='client_secrets.json', help='Path to client_secrets.json')
@click.option('--token-path', default='token.json', help='Path to store OAuth token')
@click.option('--db-path', default='migration_state.db', help='Path to SQLite state database')
@click.option('--folder', default=None, help='Name of the folder in Google Drive containing Takeout ZIPs')
def main(client_secrets, token_path, db_path, folder):
    """Google Photos Migration Tool (Takeout to Drive to Photos)"""

    if not os.path.exists(client_secrets):
        click.echo(f"Error: {client_secrets} not found. Please create OAuth 2.0 credentials in Google Cloud Console.")
        return

    creds = get_credentials(token_path, client_secrets)

    drive_mgr = DriveManager(creds)
    photos_mgr = PhotosManager(creds)
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
