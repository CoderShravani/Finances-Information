# Large document storage — final Gmail OAuth architecture

- Documents are uploaded directly from Streamlit to the authorized Gmail account's Google Drive.
- The application uses the narrow `drive.file` OAuth scope.
- The one-time OAuth setup script creates the target Drive folder, so the folder is created by the app under the same scope.
- Large files use Drive resumable uploads with a single content transfer request when practical.
- The application enforces a 1 GB maximum per uploaded file through Streamlit and a 50 GB default total document ceiling per family in the tenant-scoped database.
- The 50 GB value is configurable with `MAX_TOTAL_DOCUMENT_GB`.
- Document bytes are stored in the tenant-scoped database until Page 11 `Submit All`; Drive upload happens only during final submission. The local filesystem is not the source of truth.
- PostgreSQL is required in Railway production.

Google Drive resumable uploads support large files and allow interrupted uploads to be resumed; Google recommends retry/backoff for transient 5xx and rate-limit errors.
