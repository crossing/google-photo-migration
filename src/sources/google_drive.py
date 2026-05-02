from googleapiclient.discovery import build
import io
from src.core.interfaces import Source
from typing import List, Dict, Any

class DriveManager(Source):
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)

    def list_folders(self) -> List[Dict[str, Any]]:
        query = "mimeType = 'application/vnd.google-apps.folder'"
        results = self.service.files().list(
            q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def list_items(self, folder_id: str) -> List[Dict[str, Any]]:
        query = f"'{folder_id}' in parents and (mimeType = 'application/zip' or mimeType = 'application/x-zip' or name contains '.zip')"
        results = self.service.files().list(
            q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def get_item_stream(self, item_id: str, start_byte: int, end_byte: int) -> bytes:
        """Fetches a specific byte range from a Google Drive file."""
        request = self.service.files().get_media(fileId=item_id)
        request.headers['Range'] = f'bytes={start_byte}-{end_byte}'
        return request.execute()

    def get_item_size(self, item_id: str) -> int:
        file_metadata = self.service.files().get(
            fileId=item_id, fields='size').execute()
        size = file_metadata.get('size')
        if size is None:
            raise ValueError(f"File size not available for file_id: {item_id}")
        return int(size)

    # Keep compatibility aliases for now if needed, but the ABC uses the new names
    def list_zips_in_folder(self, folder_id):
        return self.list_items(folder_id)

    def get_file_bytes_range(self, file_id, start_byte, end_byte):
        return self.get_item_stream(file_id, start_byte, end_byte)

    def get_file_size(self, file_id):
        return self.get_item_size(file_id)
