import json
from typing import Any
from unittest.mock import MagicMock, patch

from src.auth.google_auth import DRIVE_SCOPES, PHOTOS_SCOPES, get_credentials


def test_get_credentials_existing_token(tmp_path: Any) -> None:
    token_path = tmp_path / "token.json"
    client_secrets = tmp_path / "client_secrets.json"
    client_secrets.write_text("{}")

    # Create a mock token file
    mock_creds_data = {
        "token": "fake-token",
        "refresh_token": "fake-refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "fake-id",
        "client_secret": "fake-secret",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
    }
    token_path.write_text(json.dumps(mock_creds_data))

    with patch('src.auth.google_auth.Credentials') as mock_creds_class:
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_file.return_value = mock_creds

        creds = get_credentials(str(token_path), str(client_secrets), DRIVE_SCOPES)

        assert creds == mock_creds
        mock_creds_class.from_authorized_user_file.assert_called_once_with(
            str(token_path), DRIVE_SCOPES
        )


def test_get_credentials_new_flow(tmp_path: Any) -> None:
    token_path = tmp_path / "token.json"
    client_secrets = tmp_path / "client_secrets.json"
    client_secrets.write_text("{}")

    with patch('src.auth.google_auth.InstalledAppFlow') as mock_flow_class, \
         patch('src.auth.google_auth.Credentials') as mock_creds_class:

        # Simulate no existing token
        mock_creds_class.from_authorized_user_file.side_effect = Exception("Not found")

        mock_flow = MagicMock()
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        mock_creds = MagicMock()
        mock_creds.to_json.return_value = '{"fake": "json"}'
        mock_flow.run_local_server.return_value = mock_creds

        creds = get_credentials(str(token_path), str(client_secrets), PHOTOS_SCOPES)

        assert creds == mock_creds
        mock_flow_class.from_client_secrets_file.assert_called_once_with(
            str(client_secrets), PHOTOS_SCOPES
        )
        mock_flow.run_local_server.assert_called_once()
        assert token_path.exists()
