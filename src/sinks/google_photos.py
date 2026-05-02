import os
import re
from typing import Any, BinaryIO

import requests
from googleapiclient.discovery import build

from src.core.interfaces import Sink


class PhotosManager(Sink):
    def __init__(self, creds: Any):
        # static_discovery=False is needed for Photos API
        self.service: Any = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        self.creds = creds

    def upload_item(self, filename: str, content: BinaryIO) -> str:
        """Uploads a media item to Google Photos and returns an upload token."""
        upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': self.sanitize_filename(filename),
            'X-Goog-Upload-Protocol': 'raw',
        }

        response = requests.post(upload_url, data=content, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to upload {filename}: {response.status_code} {response.text}")

    def batch_create(self, upload_tokens: list[str]) -> dict[str, Any]:
        """Finalizes the upload process by creating media items in the library."""
        new_media_items = [
            {'simpleMediaItem': {'uploadToken': token}} for token in upload_tokens
        ]
        body = {'newMediaItems': new_media_items}

        # Pyright struggles with the dynamic discovery resource
        result = self.service.mediaItems().batchCreate(body=body).execute()
        return dict(result)

    def sanitize_filename(self, filename: str) -> str:
        """Simple filename sanitization."""
        return re.sub(r'[^\w\.\-]', '_', os.path.basename(filename))

    def create_batch(self, upload_tokens: list[str]) -> dict[str, Any]:
        return self.batch_create(upload_tokens)
