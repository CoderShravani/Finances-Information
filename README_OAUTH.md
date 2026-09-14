# Gmail + Google Drive OAuth change

This version replaces the old service-account + Shared Drive document storage with Google OAuth for a personal Gmail account.

## Railway variables for Drive
- `GOOGLE_DRIVE_FOLDER_ID` — ID of a folder in the authorized Gmail account's My Drive.
- `GOOGLE_DRIVE_OAUTH_CLIENT_JSON` — the contents of the downloaded OAuth client JSON.
- `GOOGLE_DRIVE_REFRESH_TOKEN` — generated once by `google_drive_oauth_setup.py`.
- `MAX_TOTAL_DOCUMENT_GB` — keep the existing value (default 50).

The existing Apps Script variables remain unchanged:
- `GOOGLE_APPS_SCRIPT_URL`
- `GOOGLE_SYNC_TOKEN`

## One-time local OAuth setup
1. In Google Cloud, create an OAuth Client ID for a Desktop app.
2. Download the client JSON and rename it `google_drive_oauth_client.json`.
3. Put it beside `google_drive_oauth_setup.py`.
4. Install the requirements.
5. Run `python google_drive_oauth_setup.py`.
6. Sign in with the Gmail account that owns the Drive folder and approve Drive access.
7. Copy the printed refresh token into Railway as `GOOGLE_DRIVE_REFRESH_TOKEN`.

Do not commit the client JSON or refresh token to GitHub.


The application runtime uses the generated folder ID; it does not require the user to manually create or search for a Drive folder.
