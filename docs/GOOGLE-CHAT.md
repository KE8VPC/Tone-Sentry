# Google Chat setup

Tone Sentry 0.8.17 adds one-way Google Chat incoming-webhook notifications. It is a standalone integration; no OpsHub or other website is required. Notifications contain text and optional links, not MP3 attachments or interactive commands.

## 1. Create the Google Chat webhook

Use a Google Workspace account with Google Chat and incoming webhooks permitted by your administrator. Google's current quickstart specifies Business or Enterprise Workspace. In a desktop browser, open your Chat space, select its title, then Apps & integrations > Add webhooks. Name it Tone Sentry, save, and copy its complete URL. If Add webhooks is unavailable, check with your Workspace administrator.

The URL contains a secret key/token. Keep it private. Tone Sentry saves it in local destination settings; protect the receiver data folder. No separate Google password, bearer-token environment variable, OAuth setup, or service account is needed for this webhook mode.

Official instructions: https://developers.google.com/workspace/chat/quickstart/webhooks

## 2. Configure Tone Sentry

Open Settings > Destinations & actions > Add destination.

- Destination name: a readable name such as Dispatch Google Chat.
- Destination type: webhook.
- Webhook message format: google_chat. Auto also recognizes complete official Google Chat webhook URLs.
- Webhook / transcription URL: paste the complete URL including key and token.
- Delivery scope: local for a standalone receiver. Shared is for configured receiver coordination.
- Google Chat message template: customize the text. Use Preview Google Chat message to inspect it without sending.
- Trigger: choose Recording complete for a recording link, or Tone detected for an immediate text alert. Selecting both sends separate messages.
- Agency filter: select agencies, or leave all unchecked for every agency.
- Enable destination, then Save destination.

Start with this template:

```text
{agency} - {time}
Receiver: {site}
```

## 3. Link an uploaded recording

Use Recording complete as the only trigger and select your FTP/FTPS destination under Wait for successful FTP upload. Both destinations must have the same delivery scope; enable the FTP destination for the same agencies. Allow external audio sharing on those tone sets so FTP can upload.

```text
{agency} - {time}
Listen: https://your-server.example/audio/{filename_url}
```

Replace the example with the HTTPS address that serves your FTP upload directory. An FTP host/directory is not automatically a browser download URL. The link must be accessible to recipients. Use {filename_url} for URL-safe filenames; {filename} displays the actual filename. Keep the FTP remote filename template blank when using this example, so the uploaded basename matches the recording basename.

## 4. Optional transcript messages

A separate configured transcription provider is required; this integration does not transcribe audio. Create a second Google Chat destination with Transcript complete, Include transcript checked, and a template containing {transcript}. Allow external audio / transcript sharing on the associated tone sets. Wait for FTP currently applies only to Recording complete webhooks.

## 5. Verify and troubleshoot

After a real eligible page, inspect Deliveries and confirm that the message appears in the intended space. Preview does not send; safe demo and safe replay do not send external notifications. This release was tested with local/mock delivery, not a real Google account.

HTTP 400: check message size and webhook URL. HTTP 401/403/404: check webhook validity and Workspace permissions; recreate the webhook if needed. HTTP 429 or temporary server/network failures use the background retry queue. Very large messages are rejected with a clear error rather than silently cutting off a recording link; shorten the template or omit the transcript. A timeout after Google accepted a message can cause a duplicate on retry; exactly-once delivery is not guaranteed.

If no job appears, check destination enabled, trigger, agency filter, delivery scope, repeat/test suppression and transcript-sharing permission. If waiting for FTP, inspect that upload's status first. Failures do not stop tone monitoring or recording.
