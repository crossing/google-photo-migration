import os
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary']


def get_credentials(token_path: str, client_secrets_path: str, scopes: list[str]) -> Any:
    """Gets valid user credentials from storage or via the OAuth flow."""
    creds: Any = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)  # type: ignore

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path, scopes
            )
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds
