from googleapiclient.discovery import build
import io

class DriveManager:
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)

    def list_zips_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and (mimeType = 'application/zip' or mimeType = 'application/x-zip' or name contains '.zip')"
        results = self.service.files().list(
            q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def list_folders(self):
        query = "mimeType = 'application/vnd.google-apps.folder'"
        results = self.service.files().list(
            q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def get_file_bytes_range(self, file_id, start_byte, end_byte):
        """Fetches a specific byte range from a Google Drive file."""
        request = self.service.files().get_media(fileId=file_id)
        request.headers['Range'] = f'bytes={start_byte}-{end_byte}'
        return request.execute()

    def get_file_size(self, file_id):
        file_metadata = self.service.files().get(
            fileId=file_id, fields='size').execute()
        size = file_metadata.get('size')
        if size is None:
            raise ValueError(f"File size not available for file_id: {file_id}")
        return int(size)
