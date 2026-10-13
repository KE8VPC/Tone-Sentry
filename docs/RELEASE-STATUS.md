# Tone Sentry release validation and limits

## Current development release: 0.8.18

Discovery recording overlap context and optional notify-only/discovery beeps.
246 source tests passed, one skipped; isolated source application check passed
with two MP3s, three candidates and no external deliveries. Both Windows x64 packages passed isolated diagnostics, including discovery
context and the web console. Portable EXE tested alone in a fresh folder; ZIP CRCs
and SHA-256 sidecars verified. Physical speaker/output-device acceptance remains a field
check. Google Chat live acceptance is blocked by account restrictions, and
transcription development is on hold. See RELEASE-0.8.18.md.

## Previous development release: 0.8.17

Google Chat incoming-webhook notifications with standalone provider formatting,
auto URL recognition, multiline template/preview and setup guide. Source validation:
234 passed, 1 skipped; isolated source application diagnostic passed. Both Windows x64 packages passed isolated checks, including the Google Chat
formatter and web console; the portable EXE passed alone in a fresh folder.
Archive CRCs and SHA-256 checksums verified. Live Google Workspace delivery remains a
field check. See GOOGLE-CHAT.md and RELEASE-0.8.17.md.

## Previous development release: 0.8.16

Windows web listener logging crash fix, local adapter/IP references, on-demand
public-IP lookup, successful sign-in notices in Overview and side-by-side meter
controls. 231 tests passed, one skipped. Both Windows x64 packages passed isolated
checks including recovery after rejected TLS, sign-in audit, listener restart,
MP3 seeking, tone edit, local IP enumeration and synthetic reception. Portable EXE
tested alone in a fresh folder; archive CRCs/checksums verified. See
RELEASE-0.8.16.md, WEB-CONSOLE.md and VALIDATION-0.8.16.txt. Actual remote overnight
acceptance and live public-IP service availability remain field checks.

## Previous development release: 0.8.15

Optional embedded HTTPS browser console with local account setup, status,
tone editing, recording playback/download, activity, start/pause/resume/stop,
conflict checks and safe-boundary updates. 223 tests passed, one skipped.
Both Windows x64 packages passed isolated diagnostics including real local HTTPS,
authentication, MP3 seeking, pause and tone edit. Portable EXE tested alone in a
fresh folder; ZIP integrity and hashes verified. See WEB-CONSOLE.md,
RELEASE-0.8.15.md and VALIDATION-0.8.15.txt. Remote browser/network/physical audio
acceptance remains pending; automated visual browsing stopped at the generated
certificate warning. Web access is off by default and private LAN/VPN only.

## Previous development release: 0.8.14

Compact Overview: single-line summary boxes, half-width meter with gain controls
on the right, and reduced top spacing. 213 tests passed, one skipped. Two-size,
two-scaling geometry checks and both Windows package diagnostics passed; ZIP/hash
verification passed. See RELEASE-0.8.14.md and VALIDATION-0.8.14.txt. Actual remote
display/DPI remains a field check.

## Previous development release: 0.8.13

Compact Discover Tones top section, half-width meter with controls on the right,
removed reset-counter row and wrapping inline review/playback actions. Layout bounds
checked at two sizes and scaling levels. 213 tests passed, one skipped; both Windows
package diagnostics and ZIP/hash verification passed. See RELEASE-0.8.13.md and
VALIDATION-0.8.13.txt. Physical display/DPI acceptance remains a field check.

## Previous development release: 0.8.12

Completed recordings are reconciled with files on startup and before Clear deleted.
External deletions in managed audio folders now become deleted entries. Active or
encoding entries and access errors are excluded. The About beta narrative is updated.
212 source tests passed, two skipped, two dependency warnings. Both Windows package
diagnostics passed; portable tested alone, archives/checksums verified. See
RELEASE-0.8.12.md and VALIDATION-0.8.12.txt. Remote acceptance remains pending.

## Previous development release: 0.8.11

Optional monitoring on normal application launch, default off. Settings checkbox
saves immediately for the next launch; imports preserve the receiver preference.
211 source tests passed, one skipped, four warnings (dependency/Tk test cleanup).
Both Windows package diagnostics passed; portable EXE tested alone in a fresh
folder. ZIP/hash checks passed. See RELEASE-0.8.11.md and VALIDATION-0.8.11.txt.
Real remote audio-device auto-start remains a field check.

## Previous development release: 0.8.10

Optional live dispatch audio, relocated Stop playback buttons, Clear deleted on
Recordings and updated About text are packaged for Windows x64. Live output is off
by default; enable it in Playback settings. 207 source tests passed, one skipped,
two existing warnings. Folder and portable diagnostics passed with two MP3s, three
discovery candidates and zero external actions. Portable tested alone in a fresh
folder; ZIP/hash checks passed. See RELEASE-0.8.10.md and VALIDATION-0.8.10.txt.
Physical simultaneous receiver input and output remain field acceptance checks.

## Previous development release: 0.8.9

Filename time zone is selectable; new profiles use Local time, legacy settings use
UTC until changed. Local table headings and help explain start versus completion.
Stored epoch timestamps and existing files are unchanged. Source validation: 191
passed, one skip, two existing warnings. Both packaged Windows builds passed isolated
MP3 and filename/time-heading checks with zero external actions. Portable tested
alone from a fresh folder; ZIP and hash verification passed. See RELEASE-0.8.9.md
and VALIDATION-0.8.9.txt. Remote field acceptance remains pending.

## Previous development release: 0.8.8

Discover Tones includes sequence review, manual adjacent-pair or long-tone drafts,
independent discovery purity, brief dropout bridging and frequency limits.
Weekly-test starting values recovered five complete groups in the supplied sample;
agencies remain unidentified. See RELEASE-0.8.8.md and DISCOVERY-WORKFLOW.md.
183 source tests passed, one skipped, two existing warnings. Folder and portable
Windows x64 diagnostics each produced two MP3s and three discovery candidates with
zero external actions. The portable EXE passed alone from a fresh directory.
ZIP integrity and SHA256 sidecars verified; see VALIDATION-0.8.8.txt.
No running receiver or original audio was changed. Live acceptance remains pending.

## Previous development release: 0.8.7

Most settings can be saved while monitoring. Destinations apply to future jobs;
detection/recording changes wait for a quiet boundary; audio-device/channel/rate
changes reconnect automatically with a brief gap. Coordination/identity and full
settings import still require stopping. Source tests: 178 passed, one Unix-only
skip and two existing warnings. Package evidence is in VALIDATION-0.8.7.txt.
The remote receiver was not updated during development. USB-driver reconfiguration
and live RF/provider acceptance remain field checks.

## Previous development release: 0.8.6

Audio interfaces/diagnostics, delivery time/filename/details, sharing feedback and creator credit are packaged in folder and portable Windows x64 test builds. Source validation: 170 tests passed with one skip and two existing warnings, plus one additional GUI workflow test passed. Both executable diagnostics passed with two MP3s, three discovery candidates and zero external actions. See RELEASE-0.8.6.md and VALIDATION-0.8.6.txt. Actual remote USB-interface selection and error reproduction remain field checks; general live settings updates are not included.

## Previous development release: 0.8.5

Destination editor filtering and the single-file script picker are packaged in 0.8.5. The source suite passed 167 tests with one Unix-only test skipped on Windows, and both Windows builds passed isolated diagnostics. See RELEASE-0.8.5.md and VALIDATION-0.8.5.txt. Subsequent user testing confirmed script filename receipts and four agencies completing FTP and Discord audio links after enabling sharing permissions. Other missed agencies remain under tone-frequency/timing investigation.

## Previous development release: 0.8.4

The user requested a consolidated Windows build with the improved retry menu, optional FTP-dependent webhooks and readable delivery status/details. The current source suite passed 159 tests. See [0.8.4 release notes](RELEASE-0.8.4.md). The 0.7.0 Defender report remains unresolved; functional tests do not establish antivirus clearance.

## Previous development release: 0.8.3

Settings import with review, automatic local backup, receiver-local preservation, disabled imported destinations and rollback is implemented. The source suite passed 137 tests. See [0.8.3 release notes](RELEASE-0.8.3.md). Provider and radio field acceptance remain pending.

## Previous development release: 0.8.2

Flat FTP/FTPS upload directories, whitespace-free new recording names, and shared URL-safe filename placeholders are implemented. The source suite passed 130 tests, including local plain FTP uploads, retry/collision handling and exact filename/link rendering. See [0.8.2 release notes](RELEASE-0.8.2.md). Remote-server and live radio acceptance remain pending.

## Previous development release: 0.8.1

Normal masked FTP password entry with Base64 configuration storage is implemented at the user's request. Both FTP tests and deliveries use it, with legacy environment-variable compatibility. Exports omit the saved FTP password. The source suite passed 128 tests, including actual local plain FTP transfers and retries. See [0.8.1 release notes](RELEASE-0.8.1.md). Remote-server acceptance remains pending.

## Previous development release: 0.8.0

September 10, 2026. See [0.8.0 release notes](RELEASE-0.8.0.md) and [the roadmap](ROADMAP.md). Development remains unrestricted.

The final source suite passed **120 tests**. The final native executable passed its isolated diagnostic: two completed MP3s, three discovery candidates, six-character recording suffixes, matching filename templates, and legacy-default migration in a temporary test profile with identity preserved. No real receiver data or external delivery services were used. Small-window checks cover 1020x690 and 880x460 at three simulated scaling levels. Visual source review covered the Overview, Discover Tones, Settings and Help.

Windows x64 packaging and separate-folder portable acceptance are recorded in `VALIDATION-0.8.0.txt`. Live radio, prolonged operation, physical playback, remote FTP/FTPS, other machines/displays, Linux, macOS and ARM remain acceptance work. Commercial dependency/source delivery and code signing remain pending.

## Historical 0.5.0 validation

September 10, 2026 development update. The edition remains unrestricted at Mike's request. The interface uses **Tone Sentry**; the Windows executable uses **Tone-Sentry.exe**. The discovery tab is **Discover Tones**.

## New in 0.5.0

- About with the exact `Created By:  Mike Beam` credit, version and acknowledgments.
- Persistent Light/Dark settings applied without restarting the receiver engine; native OS dialogs retain OS styling.
- Optional local discovery MP3 clips: pre-roll preserving the first tone, continuous-silence stopping, configurable recording limits, bounded recording during open-carrier input, stacked-candidate association and recent-observation playback.
- Candidate audio uses existing managed storage, encoding recovery and Scheduler retention. It never queues external delivery or coordinator publication. Unconfirmed stable-tone activity may leave a clip without a candidate group.
- Explicit main-window and dialog icon assignment. Source preview visually showed the orange beacon and readable dark-theme forms. The user ended computer-use inspection with Escape before the final compiled package could receive a visual check. Additional scaling, Explorer and taskbar checks remain open.
- Offline Ed25519 registration verification and private publisher issuer utility; trusted publisher key list is empty, activation is disabled and no feature limits are enforced. Signing identity setup and license policy remain pending.
- Native compilation with Nuitka, with private build/source materials excluded from the staged binary bundle. Reverse engineering remains possible; public FFmpeg/dependency source-delivery preparation remains pending. See NATIVE-BUILD.md.

## Validation of this update

`VALIDATION-0.5.0.txt` records **89 passing tests**. The new tests verify original first-tone waveform preservation, silence/max-duration handling, shared stack clips, repeated observation links, independent configured recording, local encoding/no external jobs, retention, offline activation persistence, forged-key rejection and theme changes without replacing a running engine.

The final native-compiled **Tone-Sentry.exe** passed `runtime/native-final-050-check.json`: version 0.5.0, the Tone Sentry window title, nine tabs including Discover Tones, persistent Dark theme without engine replacement, reference/help/time-zone resources, 69 enumerated audio devices, two completed MP3 recordings, three discovery groups and zero external actions. The encoder came from the compiled bundle. This is local synthetic/package acceptance, not live RF acceptance. Native compilation used Nuitka 4.2.1 and MinGW GCC 15.2.0.

The private development archive is `dist/Tone-Sentry-0.5.0-Windows-x64.zip` (62,891,857 bytes, 1,611 files). ZIP integrity and Windows path checks passed. Staging rejected application `.py`/`.pyc`, private keys, debug symbols, runtime databases, tests and scripts. The certificate authority PEM used by HTTPS is deliberately retained. SHA-256: `9838101c307eaea44a7b0bd6ed262c730e66167543f6cc91bfdc4dddd0b5a0a3`.

The executable in the final distribution folder independently passed `runtime/staged-final-050-check.json` with the same two MP3s, three candidates and zero external actions. PE inspection confirms Windows x64, ProductName `Tone Sentry`, OriginalFilename `Tone-Sentry.exe`, version 0.5.0.0 and an embedded icon group. Embedded resources and the automated dialog check do not replace the outstanding final-binary visual icon check.

This is an executable field-test build, not a production-certified emergency dispatch system.

## Implemented

Python package/wheel, desktop and headless modes, live audio capture, two-tone/long-tone decoder, MP3 pipeline, stacked pages, repeat suppression, weekly tests, filename controls, retention, FTP/explicit FTPS, scripts, signed outgoing webhooks, generic multipart transcription, TwoToneDetect and FD Tone Notify imports, searchable tone chart, Scheduler forms, offline help, and an optional receiver coordinator with isolated archives.

## Locally verified

- Windows x64 / Python 3.10.11; desktop/forms initialize and the native console was inspected. Audio devices enumerate. No live radio input was captured as a test.
- All 20 imported tone definitions detect individually with the complete library enabled; A/B ordering, duration limits, close frequencies, near misses, noise and weak signal cases are tested.
- Actual MP3 encoding and FFmpeg decode verification; stack membership, duplicate persistence, continuation parts, replay isolation and interrupted-source recovery.
- Process locking, durable job uniqueness, stale-claim rejection and retention ownership/protection.
- Local HTTP webhook delivery, signing verification, rate-limit retry, multipart transcription contract and transcript follow-up.
- Local FTP upload with byte-for-byte readback and retry after remote acceptance.
- Two-receiver registration and association, isolated coverage groups, identity conflicts/revocation, archive isolation and preferred recording selection.

The exact latest test result is in `VALIDATION.txt`. Deprecation warnings from the test FTP server's compatibility modules are not receiver runtime failures.

## Requires further validation

- Real radio wiring/gain/squelch, fading/noisy speech, frequency drift and agency timing. Synthetic tests do not establish operational sensitivity or specificity.
- Native Linux, macOS, Apple Silicon, Windows ARM64 and Linux ARM installation/audio. A CI workflow is included but has not run remotely.
- Public HTTPS coordination, extended outages, prolonged load and geographic coverage comparisons.
- Your actual FTP/FTPS server, scripts and third-party API accounts. Local protocol/contract tests do not prove every provider compatible.
- Native service installers, application signing/notarization. Headless commands and launchers are available.

## Deferred extensions

Streaming/local-model transcription, named vendor connectors, SFTP, general incoming webhooks, audio splicing, calibrated speech-quality selection, multiple inputs inside one process, coordinator leader election, availability-first offline notifications, automatic event/transcript retention, and transcript correction history.

Use separate instances for multiple inputs. Shared coordination currently favors delayed notification over duplicate fallback delivery. Core reception and recording work without any integration or coordinator.


## Unknown-tone discovery (0.4.1)

The earlier release introduced live/WAV candidate discovery, frequency/duration measurements, repeat tracking, source labels, library-frequency filtering, reference-chart suggestions, JSON export and disabled tone-set drafts. Candidate history is capped at 1,000 groups. Version 0.4.1 stored measurements only; 0.5.0 adds optional local audio as described above. Field sensitivity and false-positive rates are not established.

## Application icon (0.4.1)

The approved orange paging beacon and radio-wave design is included in the Windows executable, Tk window/taskbar icon setup, and dialog defaults. Original artwork is retained in assets/icon-original.png. The Windows ICO includes 16, 24, 32, 48, 64, 128 and 256 pixel sizes. Source conversion is reproducible with scripts/build_icon.py using Pillow.
