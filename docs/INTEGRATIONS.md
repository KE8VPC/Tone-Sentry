# Integrations

Configure destinations under Settings > Destinations & actions. Use dropdowns, trigger/agency checkboxes, name/value rows and ordered script argument controls. Instructions are available through Help & how to in the main window. Destinations start disabled.

## Common controls

`id` is unique; `scope` is `shared` for coordinated actions or `local` for each receiver. Both scopes run locally in standalone mode. `tone_ids` restricts the agencies (empty means all). Triggers are `activation`, `recording_complete` and `transcript_complete`; FTP and transcription require recording completion. `protect_recording` defaults true.

Credentials are environment-variable references, not stored secret values. Set them before launching the process using your OS's appropriate secret/service mechanism. Default exports contain variable names. Arbitrary script arguments and provider form fields are ordinary settings: do not paste secrets into them.

Audio and transcript sharing additionally requires `allow_cloud` for every associated tone set. One disallowed agency blocks the shared recording/transcript from external delivery. Enrolled receiver-group archive synchronization is a separate, explicitly enabled trusted-group operation.

## Outgoing webhooks

HTTP POST sends a versioned JSON envelope with `schema`, stable `id`, `type`, `at` (Unix UTC seconds), source identity, tone IDs, agencies and recording ID as available. Coordinated messages also have `shared_id`. Initial activation is sent before recording/transcription completion; later events provide updates. Local filesystem paths are removed. Audio is not automatically published or attached.

`token_env` supplies a Bearer token. `header_env` maps custom header names to environment variables. `include_transcript` defaults false. Set `hmac_env` for signing:

```text
X-TonePage-Timestamp: <Unix seconds>
X-TonePage-Signature: hex(HMAC-SHA256(secret, timestamp + "." + exact body))
Idempotency-Key: <stable job ID>
```

Recipients should validate signatures/timestamps and deduplicate keys. Retries retain event bodies and logical IDs but refresh signing timestamps. Remote destinations require HTTPS; loopback HTTP is supported for tests. Redirects are rejected.

Network failures, HTTP 429 and server errors retry with bounded backoff/jitter and numeric Retry-After support. Other HTTP errors fail for review. Maximum automatic attempts: eight. An endpoint can accept a request before an acknowledgement is lost, so exactly-once effects are not guaranteed.

## FTP / FTPS

`ftp` implements plain FTP; `ftps` implements explicit TLS with certificate verification and encrypted data connections. Configure host, port, username, password environment variable and remote directory. SFTP is distinct and not implemented.

Files go to `<directory>/<source instance UUID>/<recording UUID>/`. The worker uploads under a job-specific temporary name and renames on completion. Retries recognize existing files by name and size. Remote checksums are not verified; local metadata retains source SHA-256. Plain FTP is provided for compatibility and sends credentials/audio without encryption.

## Transcription adapter

The initial provider contract is explicit:

1. Multipart HTTP POST to the configured URL.
2. MP3 field named by `file_field` (default `file`), optional scalar `fields`, optional Bearer token.
3. Successful JSON with a top-level string named by `text_field` (default `text`).

Choose a provider matching that contract or a gateway. Asynchronous provider polling, nested result extraction, OAuth refresh, streaming and local models are not implemented. No paid provider account was used for validation.

Text is stored as machine-generated and produces a transcript-complete event. `daily_limit` bounds submissions, including retries, rather than estimating a bill. Default upload limit is 25 MB (`max_bytes`). Failed work preserves its recording. Coordination queues one logical submission per selected shared recording/destination, subject to ambiguous acknowledgement retries.

## Scripts

Opt-in scripts execute explicit arguments with `shell=False`:

```json
{"id":"archive-script","kind":"script","enabled":false,"scope":"local",
 "triggers":["recording_complete"],
 "argv":["python","/absolute/path/handle_dispatch.py","{recording_id}","{path}"],
 "timeout":30}
```

Scalar event fields can substitute into individual arguments. `{path}` exists at recording completion, not activation. Stdout/stderr are discarded to prevent unbounded or secret-bearing logs; success/failure is tracked. A timeout or interrupted run is ambiguous and not automatically retried. Scripts should deduplicate by event/recording ID themselves.



## Discord and MP3 email (0.3.0)

Webhook format auto recognizes official Discord URLs and sends content plus disabled allowed_mentions. Generic event JSON remains available explicitly. Discord messages do not include MP3 attachments. See the bundled usage guide for Discord thread URLs and retry instructions.

The email destination sends the completed MP3 using SMTP STARTTLS or implicit TLS, optional username/password authentication, plain sender/recipient addresses, a subject prefix and an attachment-size limit. Credentials are environment-variable references. Recipient jobs are independent, use stable Message-ID values and retain audio-sharing and coordinated-scope rules. SMTP acceptance does not guarantee inbox delivery. Ambiguous network outcomes may result in duplicate email on retry. OAuth-only SMTP is not supported.
