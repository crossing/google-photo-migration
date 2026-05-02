import os
import re
import requests
from googleapiclient.discovery import build


def sanitize_filename(filename):
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r'[^\x00-\x7F]+', '_', name)
    return safe_name + ext


class PhotosManager:
    def __init__(self, creds):
        self.creds = creds
        self.service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)

    def upload_media_item(self, file_bytes, filename):
        """Uploads raw bytes to Google Photos and returns an upload token."""
        safe_filename = sanitize_filename(filename)
        upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-type': 'application/octet-stream',
            'X-Goog-Upload-Protocol': 'raw',
            'X-Goog-Upload-File-Name': safe_filename
        }
        response = requests.post(upload_url, headers=headers, data=file_bytes)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to upload {filename}: {response.status_code} {response.text}")

    def batch_create_media_items(self, upload_tokens):
        """Finalizes the upload process by creating media items in the library."""
        new_media_items = [
            {"simpleMediaItem": {"uploadToken": token}}
            for token in upload_tokens
        ]
        body = {"newMediaItems": new_media_items}
        return self.service.mediaItems().batchCreate(body=body).execute()
