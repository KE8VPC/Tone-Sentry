# Tone Sentry remote web console — proposed design

Original design: October 6, 2026. An embedded first implementation is now in
0.8.15. See WEB-CONSOLE.md for implemented scope, setup and differences. This
document retains the larger proposed design; not every phase is implemented.

## Purpose and first release

Provide a responsive browser console for a receiver running on Windows, Linux,
macOS or ARM. A phone, tablet or computer can check reception, edit tones, listen
to completed recordings and control detection. The receiver computer keeps doing
audio processing and storing recordings. Browser playback uses the browser user's
speakers, not the receiver's selected output device.

First-release pages:

| Page | Controls and information |
|---|---|
| Dashboard | Site, version, monitoring state, selected input/interface, input meter, last audio block age, last detected page, current recording, storage space, queued/failed delivery counts, pending settings, server connection age |
| Tone library | Search, add/edit/duplicate tone, enable/disable individual tones, two-tone/long-tone choice, frequencies, duration ranges, tolerance, repeat window, recording and external-sharing checkboxes |
| Recordings | Local date/time, agency, duration, status, filename, search/date filters, browser play/pause/seek, download and sanitized details; Clear deleted for operators |
| Activity | Detections, recording completion, audio errors, setting changes, and delivery summaries with filtering and pagination |
| Settings | Initial web-access/account settings for administrators; read-only receiver/audio/coordination summary; expanded receiver settings in a later phase |

Controls use forms, dropdowns, switches and validation messages, not editable JSON.
Small screens use stacked cards and collapsible advanced tone fields. A fixed
site/status header makes it clear which receiver is being controlled. Use explicit
state text alongside color: Monitoring, Detection paused, Stopped, Input unavailable,
Settings pending, and Disconnected.

## Receiver control semantics

- Start receiver is idempotent: starts the saved input if stopped; never toggles an
  already-running receiver off. Normal device retry/error behavior remains visible.
- Pause new detections keeps audio capture and input metering running. It disables
  configured-tone activation and discovery candidate creation; an existing dispatch
  or discovery recording finishes using its existing limits, and existing deliveries
  continue. The UI displays Paused — finishing recording until that completes.
  Resume resets detection state so a partly observed tone during the pause cannot
  trigger a page. Add a dedicated engine gate; this behavior does not exist today.
- Stop receiver explicitly ends capture and finalizes active audio as interrupted.
  Display a confirmation when an active recording would be cut short. Encoding and
  queued deliveries continue. Provide a separate result from pause.
- Enabling/disabling a tone or changing its definition uses the existing safe-boundary
  settings workflow. Saving reports Saved / waiting for quiet boundary until applied.
  Normal tone editing does not forcibly interrupt an active recording.
- Temporary detection pause is a runtime control, not a silent rewrite of every tone.
  On process restart, the existing start-monitoring preference applies; show this
  rule beside Pause. An explicit stopped receiver stays stopped until a start action
  or an application restart with startup monitoring enabled.
- Web console availability is independent of radio monitoring. Stopping the receiver
  does not stop the web service. Browser disconnect/logout never changes reception.

## One receiver owner and one control service

Keep one Engine, Store, receiver identity and instance lock for each data home.
The first implementation embeds the optional web listener in the running receiver
process, with a dedicated thread/event loop. It does not create another Engine or
write config.json independently. Closing the desktop process closes its web listener;
a later headless mode can run the same service without Tk.

Introduce ReceiverController as the sole path for desktop and web mutations:
validated tone edits, monitoring/pause commands, saved desired settings, revision
checks, operation status and audit recording. Desktop controls must use it too.
The controller calls Engine.request_settings and existing validation/persistence
rather than duplicating detection logic. It supplies safe snapshots for read APIs;
HTTP handlers never call Tk widgets or perform slow work on capture callbacks.
Desktop reads controller snapshots on its normal refresh and shows web changes.

Application operations use a serialized command queue. Return operation IDs for
potentially slow starts/stops; browsers show Pending/Applied/Failed, not premature
success. Snapshot desired and effective settings separately. Use an incrementing
revision and If-Match on edits. If another desktop/browser editor changed settings,
return a conflict and show the current revision; do not overwrite silently.
Commands accept an idempotency key to avoid duplicate actions after a retry.

A separate headless CLI mode can be added after the embedded console is stable.
A headless receiver and desktop cannot both own the same data home. Attaching the
desktop to a headless service would require an explicit client/IPC mode, not another
engine. Keep the existing coordinator delivery protocol separate from web accounts.

## Access and deployment

Web console is optional and off by default. Setup is local in Settings > Remote web
console. Show enabled state, bind address, port, access URL, certificate/proxy mode,
accounts and connected sessions. Do not open firewall ports or router forwarding
automatically. Default binding is loopback; remote use requires explicit setup.

Use a private network/VPN route initially, with HTTPS for authenticated remote
sessions (direct TLS or a configured trusted reverse proxy). A public-internet
management deployment is a later hardening/acceptance phase. Do not claim VPN
membership alone replaces application login. Never expose the existing coordinator
HTTP handler as an administration UI.

Local administrator bootstrap has no default password. Store passwords as salted
password hashes; no plain text or Base64 password storage for web accounts. Use
server-side sessions, HttpOnly/Secure/SameSite cookies, CSRF protection on changes,
login throttling, logout/inactivity expiry and session revocation. Reject unexpected
Host/Origin values and keep browser requests same-origin. Trust proxy headers only
from specifically configured proxies. Disable caching of private API/audio responses.
The exact maintained HTTP/auth stack and dependency licenses must be reviewed at
implementation time; do not build a new production HTTP parser around the current
coordinator's basic request handler.

Roles:
- Viewer: status, activity, authorized recordings/playback/download.
- Operator: viewer access plus tone edits, start/pause/resume/stop and Clear deleted.
- Administrator: operator access plus web accounts, roles and access configuration.

Enforce roles on server endpoints, including audio. Never return full configuration,
FTP passwords, webhook URLs/tokens, email secrets or arbitrary local filesystem paths.
Sanitize recording JSON because its encoding settings/path can disclose local paths.
Audit who changed what, when, receiver identity, previous/new non-secret values,
request ID and result. Do not log credentials or session tokens.

## Proposed API contract

All routes require the indicated session/role; only login and a minimal liveness
response may be unauthenticated. No raw filesystem paths accepted from a browser.

| Route | Purpose |
|---|---|
| POST /api/session; DELETE /api/session | Sign in / sign out |
| GET /api/status | Snapshot, desired/effective state, server time, current config revision |
| GET /api/events/stream | Bounded server-sent status/event updates; reconnect using event IDs |
| POST /api/receiver/start | Idempotent start operation |
| POST /api/receiver/pause; /resume; /stop | Explicit operations with role and CSRF checks |
| GET /api/operations/{id} | Completion, failure, deferred boundary and actionable errors |
| GET /api/tones | Tone list and revision |
| POST /api/tones | Create a validated tone with stable internal ID |
| PATCH /api/tones/{id} | Reviewed field updates, including enabled, with If-Match |
| DELETE /api/tones/{id} | Operator-confirmed removal; preserve historical event metadata |
| GET /api/recordings | Paginated/filterable safe metadata |
| GET /api/recordings/{id} | Sanitized details |
| GET /api/recordings/{id}/audio | Authorized MP3 stream with byte-range support |
| POST /api/recordings/clear-deleted | Reconcile missing files and hide deleted entries |
| GET /api/activity; GET /api/deliveries | Paginated history and sanitized delivery summaries |

Audio endpoints resolve recording IDs through the Store, enforce managed paths
including symlink containment, allow only finished MP3s, and recheck availability
when opening. Return a clear unavailable/deleted response if cleanup wins a race.
Do not expose WAVs still being written or mount the audio folder as an unauthenticated
static directory. Support seeking with valid Range/206/416 responses and limit
concurrent streams and request sizes. Merely opening a page must not autoplay audio;
users press Play, in accordance with normal browser behavior.

Status updates are throttled (roughly 2–4 per second for meters), with bounded queues
per browser. Slow clients can drop meter updates; they must never back up capture.
Paginate all lists. Display the last successful update age and a Disconnected banner;
disable command controls when state is stale. Read-only fallback polling is acceptable.
Use server timestamps in UTC with explicit offsets; display receiver-local time as
the primary clock, labeled with its zone, and optionally browser-local time. Filename
start time and recording completion remain distinct.

## Implementation phases and acceptance

1. Shared controller and read-only authenticated console: accounts, dashboard,
   status freshness, activity, recording list and browser playback. Validate one
   engine per home, redaction, audio ranges, access control and no capture stalls.
2. Tone editing and controls: form validation, optimistic concurrency, desktop sync,
   start/pause/resume/stop, deferred edits, audit entries and Clear deleted. Test
   partially received tones at pause/resume, active recording completion, failed
   persistence, disconnected input, duplicate requests and simultaneous editors.
3. Remote deployment packaging: desktop enable/disable setup, TLS/proxy/VPN guide,
   headless launch mode, Windows portable packaging and Pi package updates. Test
   session expiry, device startup, disconnect/reconnect, UI responsiveness under
   concurrent audio downloads and actual phone/tablet use against a receiver.
4. Optional expansion: discovery review/drafts, delivery retry/cancel, scheduler,
   richer input/settings controls, multiple-receiver dashboard and browser live audio.

Browser live audio is separate from the implemented receiver-speaker feature and
is not included in the first release. Recording deletion, scripts/command execution,
credential editing, OS reboot and remote software updates are also outside the
first release. These need explicit designs rather than a generic remote shell.

Current development licensing remains unrestricted. Before enforcing paid tiers,
clarify whether remote access itself is free/full; do not assume that one receiver's
web console is multi-receiver coordination. When limits are implemented, enforce
the same rules in the controller for desktop and web. No licensing change is made
by this design.
