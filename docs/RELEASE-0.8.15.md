# Tone Sentry 0.8.15 — remote web console beta

The Windows desktop receiver can now host an optional authenticated HTTPS console
for another computer, phone or tablet on a private LAN/VPN. Enable it in
Settings → Remote web console; it is off by default and has no default password.

- Status with receiver-local time, audio level/age, input details and pending settings.
- Tone library forms: add, edit, delete, enable/disable, frequency/timing, repeat
  window, recording and external sharing. Existing advanced settings are preserved.
- MP3 list/search, browser playback with seeking, downloads and safe metadata.
- Activity list and remote command audit events.
- Start, pause/resume detection, and confirmed stop. Pause also appears in Overview.
- Viewer/operator/admin accounts configured locally, HTTPS, session expiry/logout,
  request-origin and CSRF checks, login throttling and managed audio path checks.
- Serialized commands use the existing desktop owner and receiver. Concurrent edit
  conflicts and open desktop dialogs prevent silent stale settings overwrites.

Read **docs/WEB-CONSOLE.md** for setup, certificate fingerprint verification,
network/firewall guidance, account roles and operational limits. Windows Firewall
and router settings are not changed automatically.

Closing the desktop closes web access. Web support is not added to headless `run`
in this release. Public-internet hosting, browser live audio, discovery/scheduler/
destination web editing, browser account administration and Pi rebuilds remain
future work. Existing data and unrestricted development licensing are preserved.

See VALIDATION-0.8.15.txt for source and packaged test results. Local HTTPS/API tests
do not establish remote network, browser certificate acceptance, phone layout,
physical audio, overnight or public-network acceptance.
