# Security Fixes Applied — Final Hardened Build

1. **HMAC request authentication**
   - `GOOGLE_SYNC_TOKEN` is never serialized into the outbound request.
   - Streamlit signs the exact compact JSON payload with HMAC-SHA256.
   - Apps Script verifies that signature before processing any tenant data.
   - The signature covers the complete payload, including `tenant_id`, `submission_id`, records, attachments and reminder configuration.

2. **Replay protection**
   - Every export receives a fresh 128-bit nonce and a 10-minute timestamp window.
   - Apps Script stores a tenant-scoped nonce in the `Request_Nonce` sheet for the 10-minute authentication window and removes expired entries.
   - Nonces are consumed under `ScriptLock`, preventing concurrent duplicate processing.
   - A legitimate retry gets a new nonce but keeps the same submission ID, so durable `Sync_Log`-based submission deduplication remains safe.

3. **PostgreSQL legacy settings migration**
   - Detects the old `app_settings` primary key on `key`.
   - Renames the legacy table instead of attempting an invalid nullable composite primary key.
   - Creates the correct `(tenant_id, key)` primary key.
   - Copies only rows that already have a tenant ID; unassigned legacy rows remain isolated.
   - Migration errors are no longer silently ignored.

4. **SQLite legacy settings migration**
   - The legacy table is rebuilt when its primary key is still only `key`.
   - Migration errors are allowed to surface instead of being silently swallowed.

5. **Reflected HTML hardening**
   - The signed-in tenant email is HTML-escaped before rendering through Streamlit's unsafe HTML path.

6. **Single-request architecture preserved**
   - The Streamlit application still contains exactly one `urllib.request.urlopen()` call.
   - Google is contacted only by the explicit final export action.
   - No gspread, SMTP, Excel export, or per-page Google calls were introduced.
