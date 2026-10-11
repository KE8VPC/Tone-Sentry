# Tone Sentry 0.8.0 — unrestricted development release

## Operator changes

- Compact dark header: tagline beneath the name, six actions on one row, shorter button labels when needed, and a shared receiver/playback status row. Reduced padding and card height leave more space for tab content. Settings, Scheduler and About retain access through scrolling when their content exceeds the window.
- Slim shared input meter with a prominent orange gain handle, tricolor levels, peak/clipping indication, Auto gain, Reset and Save. The gain pipeline is unchanged.
- Condensed Site, Instance ID, Mode and Coordinator Status lines on Receivers.
- New local MP3 filenames end in a six-character random ID. Atomic file reservations and a persisted recording-to-filename mapping protect against collisions and keep retries on the same filename. Internal UUIDs and existing recordings are preserved. Custom filename templates can still explicitly include full IDs; coordinator archive naming remains separate.
- `{filename}` is shared across Discord formatting, generic webhook message templates, email subject/body templates, FTP remote filename templates and script arguments. It is the completed MP3 basename, without the local path, and is empty before completion. Optional new templates left blank preserve previous behavior. Queued jobs retain saved destination settings. Filename text does not attach audio to Discord.
- FTP/FTPS Test FTP connection checks unsaved values, login and entry into the configured directory without creating files or directories. It does not test upload permission or the data-transfer channel. Password-reference fields are masked on screen; they still expect environment-variable names and are not encrypted by masking.
- Help now follows setup, audio/tone configuration, recording/discovery/playback, schedules and integrations, multiple receivers, appearance, troubleshooting and reference. Section navigation and readable formatted headings are retained.

## Windows data-folder transition

The new default is `%USERPROFILE%\ToneSentryData`. When only the legacy default exists, the application locks it, copies it to a staging folder, updates paths in JSON and SQLite records, verifies the copied configuration/database integrity, then publishes the new folder. The original remains for recovery. No migration is performed on the developer's real receiver data during testing.

Close older receivers before upgrading. Migration needs enough disk space for both copies and can take time with a large audio archive. Do not run older versions against the retained legacy copy: its queued delivery state becomes outdated. New default sessions hold the old receiver locks too. Explicit `--home` folders are not migrated; this version refuses to use a marked legacy backup as an active receiver. Two independent default folders require an explicit folder selection instead of an automatic merge. Failed staging copies are retained for inspection; a missing completed destination requires recovery rather than automatically replaying stale legacy jobs.

## Verification and remaining acceptance

The source suite passed 120 tests. Source Overview, Discover Tones, Settings and the reordered Help were visually reviewed in an isolated preview. A theme override that restored oversized tab padding was corrected; the tab padding is checked in both themes. Header checks also cover the reduced 880x460 minimum size across the three simulated scaling levels. Help uses concise navigation labels so section choices remain readable.

The native executable passed its isolated packaged diagnostic: two completed MP3s, three discovered candidates, six-character filenames, matching filename placeholders, test-profile migration with preserved identity, bundled help/resources, and device enumeration. No live input or external deliveries were used.

Automated checks include existing receiver/integration behavior; source GUI controls and theme changes; compact-header geometry at 1020x690 with Tk scaling corresponding to 100%, 125% and 150%; short-name collisions/restart; directory migration, active locks, ambiguous folders and interrupted copying; shared templates; FTP validation and credential masking. Simulated scaling is not a visual acceptance test on every monitor.

Packaged diagnostics run with isolated data, synthetic input and no external notifications. Live RF, prolonged operation, physical playback, remote FTP/FTPS, coordinated provider deliveries and different-machine/display behavior still require operator testing. The supplied artifacts target Windows x64. Linux, macOS and ARM builds remain unverified.

Development remains unrestricted. Code signing, publisher registration policy, and commercial third-party/source-distribution preparation are still pending. Native compilation makes source recovery harder but cannot prevent reverse engineering.
