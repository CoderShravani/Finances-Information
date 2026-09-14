# Security / API Audit — Final Hardened Multi-Tenant Build

## Tenant isolation
- [x] Explicit authenticated tenant account required before any family data is shown.
- [x] Random tenant ID stored server-side in session state.
- [x] Records scoped by tenant ID.
- [x] Record values scoped by tenant ID and tenant-matched joins.
- [x] Attachments scoped by tenant ID.
- [x] Family contacts scoped by tenant ID.
- [x] Reminder settings scoped by tenant ID.
- [x] Reminder log / attempts scoped by tenant ID.
- [x] Google export payload contains only the current tenant's records and attachments.
- [x] Google Apps Script tags every data/reminder/contact/config/status row with tenant ID.
- [x] Google reminder job processes tenant-specific active submissions and recipients.

## Authentication
- [x] Passwords are salted with a random 16-byte salt.
- [x] Passwords are hashed with `hashlib.scrypt`.
- [x] Constant-time digest comparison via `hmac.compare_digest`.
- [x] Minimum password length: 12 characters.
- [x] Failed-login rate limit per email: 5 recent failures within a 15-minute lockout window.
- [x] No plaintext password is written to database, Sheets, Drive, logs, or payloads.

## Google request security
- [x] Exactly one Streamlit `urllib.request.urlopen()` call exists for explicit final export.
- [x] Sync token is sent only in that final request body.
- [x] Sync token is never persisted to application data or Google Sheets.
- [x] Request timestamp has a 10-minute acceptance window.
- [x] Submission ID is validated as an opaque 32-hex identifier.
- [x] Tenant ID is validated as an opaque 32-hex identifier.
- [x] Apps Script checks submission ownership before returning duplicate success.
- [x] Script lock serializes submissions.
- [x] Successful duplicate submissions do not rewrite data or attachments.

## Deployment
- [x] PostgreSQL can be enforced for Railway with `REQUIRE_POSTGRES=1`.
- [x] Legacy Google sheets are preserved instead of being destructively rewritten when the schema changes.
- [ ] HTTPS must be used for the Railway app and Apps Script web app in production.
- [ ] The Google Sheet and Drive parent folder must remain accessible only to trusted administrators; tenant isolation does not make a manually shared master Google Sheet tenant-private.

## Scope note
No software can honestly be certified as “100% secure.” This audit verifies the implemented isolation and security controls in this package; production security also depends on deployment configuration, credentials, HTTPS, database access controls, backups, and administrator permissions.


## Final hardening fixes applied

- [x] Shared Google sync secret is no longer transmitted as a payload field; it is used only as the HMAC-SHA256 signing key.
- [x] Apps Script verifies the HMAC over the exact compact JSON payload before processing it.
- [x] Apps Script consumes a tenant-scoped nonce under the script lock and rejects reuse for 10 minutes.
- [x] PostgreSQL legacy `app_settings` migration now detects the old single-column primary key, preserves legacy rows in a separate table, and rebuilds the tenant-scoped table instead of silently swallowing a failed composite-key migration.
- [x] Tenant email is HTML-escaped before being inserted into Streamlit's unsafe HTML sidebar.
- [x] SQLite legacy settings migration no longer silently suppresses migration failures.

These controls improve the security boundary but do not constitute a guarantee of absolute security. Direct access to the master Google Sheet remains administrative access to all tenant rows.
