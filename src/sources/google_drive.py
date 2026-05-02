from typing import Any

from googleapiclient.discovery import build

from src.core.interfaces import Source


class DriveManager(Source):
    def __init__(self, creds: Any):
        self.service = build('drive', 'v3', credentials=creds)

    def list_folders(self) -> list[dict[str, Any]]:
        query = "mimeType = 'application/vnd.google-apps.folder'"
        results = self.service.files().list(
            q=query, fields="nextPageToken, files(id, name)"
        ).execute()
        files = results.get('files', [])
        return [dict(f) for f in files]

    def list_items(self, folder_id: str) -> list[dict[str, Any]]:
        query = (
            f"'{folder_id}' in parents and (mimeType = 'application/zip' or "
            f"mimeType = 'application/x-zip' or name contains '.zip')"
        )
        results = self.service.files().list(
            q=query, fields="nextPageToken, files(id, name, size)"
        ).execute()
        files = results.get('files', [])
        return [dict(f) for f in files]

    def get_item_stream(
        self,
        item_id: str,
        start: int | None = None,
        end: int | None = None
    ) -> bytes:
        headers: dict[str, str] = {}
        if start is not None and end is not None:
            headers['Range'] = f'bytes={start}-{end}'

        request = self.service.files().get_media(fileId=item_id)
        if headers:
            # We know headers is not None here and contains only str keys/values
            request.headers.update(headers)  # type: ignore
        return bytes(request.execute())

    def get_file_size(self, file_id: str) -> int:
        file_metadata = self.service.files().get(fileId=file_id, fields='size').execute()
        return int(file_metadata.get('size', 0))

    def get_folder_id_by_name(self, folder_name: str) -> str | None:
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        if files and 'id' in files[0]:
            return str(files[0]['id'])
        return None

    def list_zips_in_folder(self, folder_id: str) -> list[dict[str, Any]]:
        return self.list_items(folder_id)
