# Large storage audit — final Gmail OAuth package

## Limits
- Per-file Streamlit upload ceiling: 1 GB via `.streamlit/config.toml`.
- Default total document ceiling: 50 GB per family via `MAX_TOTAL_DOCUMENT_GB`.

## Storage flow
- Page 2–10 saves are local database saves; selected document bytes are stored transactionally in the tenant-scoped database.
- Page 11 `Submit All` uploads pending documents sequentially to Google Drive.
- After all document uploads succeed, the app performs the single Apps Script HTTPS POST for structured data, Drive links, and reminder configuration.

## OAuth
- Personal Gmail/My Drive OAuth replaces the previous service-account/Shared Drive architecture.
- The app uses `drive.file`. The one-time setup script creates the target folder under that same OAuth grant.

## Reliability
- Drive uploads use resumable media upload and bounded exponential backoff for transient failures.
- Apps Script submission retries use a fresh HMAC nonce/timestamp on every HTTP attempt, while the submission ID provides idempotent deduplication.

## Production requirement
- Railway must use PostgreSQL (`REQUIRE_POSTGRES=1`).
- The OAuth consent screen should be moved to production for long-lived refresh-token operation.


## Consistency fixes applied
- Family_Data and Reminders now use current-state replacement per tenant; Sync_Log remains the historical audit trail.
- Sidebar navigation now uses Dashboard / Family Pages / Google Sync as mutually exclusive destinations.
- Runtime Drive setup error now points to google_drive_oauth_setup.py.
- Local .env.example defaults REQUIRE_POSTGRES to 0; Railway production remains 1.
