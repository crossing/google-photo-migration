import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/photoslibrary'
]

def main():
    print("Initializing Flow...", flush=True)
    try:
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
        print("Starting local server...", flush=True)
        creds = flow.run_local_server(port=0, open_browser=False)
        print("Authentication Successful!", flush=True)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
        print("token.json saved.", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)

if __name__ == "__main__":
    main()
