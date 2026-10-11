# Tone Sentry remote web console — 0.8.16 beta

The optional browser console lets you check a receiver, edit its tone library,
listen to completed MP3s, and start, pause or stop detection from another device.
It runs inside the Windows desktop application and uses the same engine and data.
No second receiver, data copy, coordinator or cloud account is needed.

## Set up on the receiver computer

1. Open **Settings → Remote web console**.
2. For access from another device, set **Listen address** to `0.0.0.0`.
   `127.0.0.1` allows only browsers on the receiver itself.
3. Set **Receiver IP or hostname** to the receiver's LAN or VPN IPv4 address,
   for example `192.168.1.50`. Enter the address only, without a port or slash.
   Use an address that your other computer/phone can reach. A DHCP reservation
   helps keep the address stable. This entry controls the allowed browser host
   and the certificate name; it is not an automatic network discovery service.
4. Leave **HTTPS port** at `8767` unless that port is already in use.
5. Enter an account username, a new password of at least 12 characters, and select
   **admin**. There is no default account or password.
6. Check **Enable HTTPS web console**, then **Save and apply web access**.
7. Reopen this settings dialog. It shows the active URL and certificate SHA-256.
8. On your other device, open the displayed URL, for example
   `https://192.168.1.50:8767`. The `https://` prefix is required.
9. The first visit will warn about an untrusted certificate, because this beta
   creates a certificate locally instead of obtaining one from a public authority.
   View the browser's certificate details and compare its SHA-256 fingerprint
   against the fingerprint on the receiver. Only accept it if they match and you
   have reached your intended receiver. Then sign in with your new account.

Keep Tone Sentry open. A stopped receiver can still be controlled from the web;
closing the application closes the web listener. Web access starts again at the
next desktop launch if enabled. The existing monitoring-on-startup preference
separately controls whether audio capture starts.

## Network access and troubleshooting

This beta is for a private LAN or a VPN. It does not configure Windows Firewall,
router port forwarding, public hosting or a reverse proxy. If Windows asks whether
to allow the app through the firewall, allow only the private network you intend
to use. You may need an inbound TCP rule for your chosen port, restricted to your
LAN/VPN. Do not forward this management port onto the public internet.

If the page cannot connect, check the receiver's current IP, listen address, port,
firewall, and whether both devices are on the intended network. `localhost` on your
phone means the phone itself, not the receiver. Stop monitoring is unrelated to
stopping the web listener. To turn web access off, clear its Enable checkbox and save.

If the browser says the host was rejected, use the exact address saved in Settings.
Alternate DNS names are not automatically accepted. Loopback `localhost` and
`127.0.0.1` remain accepted for local use. This release supports IPv4 listening.

Changing the browser hostname regenerates the certificate; compare its new
fingerprint. Certificates last one year. To renew an expired one, disable web
access, remove only `web-tls/host.txt` in your data folder, then re-enable it.
The next start creates a replacement certificate and fingerprint.

## Accounts

- **Viewer:** status, tone list, activity, recording details, playback and download.
- **Operator:** viewer functions plus tone changes, start/pause/resume/stop and
  Clear deleted.
- **Administrator:** the same browser controls as Operator in this first release.
  Account creation/removal and access configuration are done locally in Settings.

Add another account by reopening setup, entering a different username/password and
selecting its role. Reusing a username replaces that account's password and role.
Leave both fields blank to retain accounts unchanged. Use Remove account to remove
one. At least one administrator is required while web access is enabled.

Saving access settings restarts the listener and signs everyone out. Sessions also
expire after 30 minutes without requests or 12 hours overall. An actively displayed
dashboard polls status, which counts as activity. Closing a tab does not necessarily
sign you out; use Sign out on shared devices. Repeated failed logins are throttled.

Account hashes and listener settings are kept separately in `web-access.json`.
Certificate/key files are in `web-tls/`. They are not included in normal receiver
settings exports. Web passwords use salted scrypt hashes, not the Base64 option
used for FTP. The certificate private key relies on protection of the receiver's
Windows account/data folder. Do not share that folder or copy web accounts/keys
into a distributed test package.

## Status and monitoring controls

- **Start monitoring:** starts the saved input; safe to click when already running.
- **Pause detections:** keeps input capture and metering running, stops new known
  activations and discovery candidates, and allows current audio to finish using
  its silence/maximum limits. It does not cancel queued deliveries.
- **Resume detections:** clears partial tone state and resumes detection. You can
  also pause/resume from the desktop Overview. Pause is temporary; it clears on
  application restart. A pause remains in effect across Stop/Start in one session
  until you choose Resume.
- **Stop monitoring:** ends capture; its confirmation warns that active recordings
  may be finalized as interrupted. Pending encodes and deliveries continue.

The dashboard shows receiver-local time including UTC offset, input sample rate,
channel, level, last input age, dropped blocks and pending settings. Browser status
polls every two seconds while visible. Stale status disables editing controls;
commands already submitted are tracked by operation ID. Leaving the browser does
not stop the receiver.

## Tone editing

Select Tone library, then Edit or Add tone set. Use numeric frequency/duration
fields, a tone type selector and checkboxes. Saves use the same validation and
quiet-boundary application as desktop edits. **Saved / waiting** means a current
page or recording is being allowed to finish, not that the edit was lost.

New tones default to disabled with external sharing off. Existing weekly schedules,
per-tone recording overrides and imported percentage frequency tolerances are
preserved. Imported percentage tolerance is explained in the editor and still takes
precedence over Hz tolerance. Advanced settings remain in the desktop editor.

If settings changed in another browser or on the desktop, the edit is rejected.
Reload tones and review your changes. While any desktop dialog is open, remote
mutations fail with a clear message; close the dialog and retry. This prevents
an older open desktop form from silently overwriting a remote edit.

## Recordings and activity

Search recordings by agency/filename, move through 50-entry pages, and press Play.
The browser player supports pause/seek and uses the browser device's speakers.
Download saves that MP3 to your browser device. There is no automatic playback.
Recordings still capturing/encoding are not playable until complete.

Times use the receiver's local zone, not the browser's zone. Filenames can still
use UTC if that is your receiver setting. Details are intentionally a safe subset
of JSON: no local full paths, destination secrets or raw recording configuration.
Clear deleted checks managed paths and hides entries for missing completed files;
it does not delete audio. If cleanup removed an MP3, refresh the list or clear
deleted. Activity lists event type, time, agencies and remote action audit results;
detailed errors remain available on the desktop.

## Scope of this beta

Implemented: embedded HTTPS, local accounts with server-side sessions, status,
known tone CRUD, recording list/play/download, activity, pause/resume/start/stop,
safe-boundary edits, edit conflicts, bounded command queue and local setup.

Not included: web discovery review, web scheduler/destination administration,
browser live audio, remote file deletion, multi-receiver dashboard, browser account
administration, web support in the headless `run` command, public-internet hosting
or updated Pi packaging. Closing the desktop closes the service.

The first implementation serializes HTTP commands on the existing desktop owner
thread, with published snapshots for HTTP readers. HTTP threads never call Tk or
create another Engine. Long desktop operations can delay commands/status updates
but do not run on the audio capture callback. Polling is used rather than SSE.

## Implementation references

Flask serves the application through Cheroot's WSGI server with its built-in TLS
adapter. Flask/Werkzeug provide conditional MP3 responses for byte-range seeking.
The release includes notices for these dependencies and their transitive packages.
See the [Flask security guide](https://flask.palletsprojects.com/en/stable/web-security/),
[Flask send_file API](https://flask.palletsprojects.com/en/stable/api/#flask.send_file),
and [Cheroot TLS adapter](https://github.com/cherrypy/cheroot/blob/main/cheroot/ssl/builtin.py).


## 0.8.16 connection recovery and address reference

Web setup now lists local IPv4 addresses by adapter name and connected state.
Refresh local IPs rereads the local interfaces. Look up public IP contacts
https://api.ipify.org only when you click it; it runs in the background with short
connection/read timeouts and does not change any listener setting. Offline/service
failures show Unavailable. A VPN can change the reported public address. A public
IP does not imply that this console is accessible from the internet.

Successful sign-ins create one Overview event with username, connecting IP and
receiver-local date/time. Background polling and playback do not flood the log.
Connection IP is the direct peer address, not an untrusted forwarded header.

The Windows windowed listener now survives rejected certificate handshakes and
connection errors when no console stderr is available. Connection warnings are
throttled and sanitized. If the listener stops for another reason, its exception
class appears in Settings and Overview. Save and apply web access restarts it.
The Open current web console button reports when the listener is stopped.

The address reference uses psutil's local interface enumeration; public lookup
uses ipify's plain-text endpoint. References: https://psutil.readthedocs.io/stable/
and https://www.ipify.org/ . The package includes the psutil license notice.
