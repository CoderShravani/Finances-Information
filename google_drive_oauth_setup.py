import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']

client_path = Path('google_drive_oauth_client.json')
if not client_path.exists():
    raise SystemExit(
        'Place your downloaded Google OAuth client JSON next to this script '
        'and name it google_drive_oauth_client.json.'
    )

client_config = json.loads(client_path.read_text(encoding='utf-8'))
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

service = build('drive', 'v3', credentials=creds, cache_discovery=False)
folder = service.files().create(
    body={
        'name': 'My Family Should Know Documents',
        'mimeType': 'application/vnd.google-apps.folder'
    },
    fields='id,name,webViewLink'
).execute()

print('\nOAuth setup complete.')
print('GOOGLE_DRIVE_FOLDER_ID=')
print(folder.get('id') or '')
print('\nGOOGLE_DRIVE_REFRESH_TOKEN=')
print(creds.refresh_token or '')
print('\nThe folder above was created by this app, so it is directly usable with the drive.file scope.')
print('Keep the refresh token secret. Do not paste it into chat or commit it to Git.')
