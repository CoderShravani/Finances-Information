# My Family Should Know — Complete Gmail OAuth Production Package

This package preserves the complete hardened application and changes only the Google Drive authentication/storage architecture from Service Account + Shared Drive to Gmail OAuth + the authorized Gmail account's My Drive.

## Preserved functionality
- Complete 11-page / 32-section family record schema.
- Professional Streamlit UI and page navigation.
- Multi-tenant account isolation.
- Password authentication using salted `hashlib.scrypt` hashes.
- Failed-login rate limiting.
- PostgreSQL on Railway, with SQLite fallback for local development.
- Local saves and duplicate-save protection.
- Page 11 `Submit All` final workflow.
- Direct Google Drive document storage with resumable uploads and retry/backoff.
- 50 GB default total document limit per family, configurable with `MAX_TOTAL_DOCUMENT_GB`.
- 1 GB actual per-file upload limit.
- Google Drive + Sheets final sync through the single final Apps Script HTTPS POST.
- HMAC authentication, nonce/replay protection, submission deduplication and Apps Script locking.
- Family contacts and reminder configuration.
- Daily Apps Script reminder engine.
- Sensitive card fields are not stored.
- No Excel export.
- Railway deployment files and configuration.

## Architecture

`Streamlit UI -> PostgreSQL/Railway -> Gmail OAuth -> Google Drive`

and, only on final submission:

`Streamlit -> one Apps Script HTTPS POST -> Google Sheets + reminder configuration`

Documents are uploaded directly to Drive and only their Drive metadata/links are included in the final Apps Script payload.

## Google Drive OAuth setup

Set these Railway variables:

- `GOOGLE_DRIVE_FOLDER_ID` — folder ID created by the one-time OAuth setup script in the authorized Gmail account's My Drive.
- `GOOGLE_DRIVE_OAUTH_CLIENT_JSON` — complete OAuth client JSON.
- `GOOGLE_DRIVE_REFRESH_TOKEN` — generated once with `google_drive_oauth_setup.py`.
- `MAX_TOTAL_DOCUMENT_GB=50` — default family total document limit.
- `DRIVE_UPLOAD_CHUNK_MB=32` — optional upload tuning.

The old service-account variables `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_DRIVE_SHARED_DRIVE_ID` are intentionally removed because this version uses Gmail OAuth.

## One-time OAuth setup

1. Create an OAuth Client ID in Google Cloud for a Desktop app.
2. Download the client JSON as `google_drive_oauth_client.json` beside `google_drive_oauth_setup.py`.
3. Install `requirements.txt`.
4. Run `python google_drive_oauth_setup.py`.
5. Sign in with the Gmail account that should own the documents.
6. Approve Drive access. The setup script creates the `My Family Should Know Documents` folder.
7. Put the printed `GOOGLE_DRIVE_FOLDER_ID` into Railway.
8. Put the printed refresh token into Railway as `GOOGLE_DRIVE_REFRESH_TOKEN`.
9. Put the JSON contents into `GOOGLE_DRIVE_OAUTH_CLIENT_JSON`.

Never commit the OAuth client JSON or refresh token to GitHub.

## Google Sync / Apps Script

1. Open the target Google Sheet and open Extensions -> Apps Script.
2. Paste `Code.gs`.
3. Set Apps Script properties:
   - `SPREADSHEET_ID`
   - `SYNC_TOKEN`
4. Deploy as a Web App and use its URL as `GOOGLE_APPS_SCRIPT_URL`.
5. Set the same secret as `GOOGLE_SYNC_TOKEN` in Railway.
6. Run `ensureReminderTrigger()` once to authorize the daily reminder trigger.

## Railway variables

Required:
- `DATABASE_URL`
- `REQUIRE_POSTGRES=1` (production Railway; local `.env.example` defaults to `0`)
- `GOOGLE_APPS_SCRIPT_URL`
- `GOOGLE_SYNC_TOKEN`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_DRIVE_OAUTH_CLIENT_JSON`
- `GOOGLE_DRIVE_REFRESH_TOKEN`

Optional:
- `MAX_TOTAL_DOCUMENT_GB=50`
- `DRIVE_UPLOAD_CHUNK_MB=32`

## Upload limits

The application enforces **1 GB per uploaded file** and **50 GB total document storage per family by default**. The 1 GB per-file setting is enforced by Streamlit's uploader configuration, not merely by CSS text. The 50 GB total is enforced by the application's tenant-scoped database quota.

## Important OAuth production note

For a long-lived deployment, do not leave the Google OAuth consent screen in **Testing**. Google documents that external/testing refresh tokens can expire after 7 days; move the OAuth app to **In production** for the production deployment.

## Important production note

Pending document bytes are stored transactionally in the tenant-scoped database until Page 11 `Submit All`; the local filesystem is not the source of truth. This preserves the intended final-submission workflow across Railway restarts while keeping Drive uploads deferred until final submission. For production, PostgreSQL must be used on Railway. A separate object-storage/background queue is not required for document durability in this version.


## Google Sheet data model

`Family_Data` and `Reminders` are **current-state sheets**: each successful final sync replaces that tenant's previous rows with the latest complete snapshot. Historical submissions remain available in `Sync_Log` and `Tenant_Status` for operational auditing. This prevents stale older family data from remaining alongside the current record.

## Navigation model

The sidebar has three mutually exclusive destinations: `Dashboard`, `Family Pages`, and `Google Sync`. Selecting any Page 2–11 automatically switches the top-level destination to `Family Pages`, so the navigation state always matches the content being displayed.
