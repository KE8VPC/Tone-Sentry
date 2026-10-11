# Tone Sentry 0.6.0 — unrestricted development release

## Changes

- Overview has an overlaid gain handle and tricolor post-gain sample-peak meter. Green extends to -12 dBFS, yellow to -3 dBFS and red to full scale. Peaks hold for approximately 300 ms, and overload warnings hold for 1.5 seconds. Input already reaching full scale is flagged even when software gain is low. This is not a calibrated loudness or true-peak meter.
- Gain changes apply to reception without replacing the engine, save after dragging, and can be reset to 1×. The meter clears in standby. Audio is amplified once before detection and recording.
- Overview Clear all, Deliveries Clear completed, and Discover Tones Clear candidates hide history persistently. Internal records remain for duplicate suppression, job uniqueness, references and recording access. New observations can make a hidden candidate reappear. Pending, failed, active and ambiguous deliveries are preserved.
- Destinations have editable display names in settings and delivery lists. Their internal IDs stay stable, including existing job snapshots. Duplicate display names are possible; use distinct descriptive names.
- New local recordings and their sidecar JSON files go directly into `audio/` without a receiver-ID subfolder. Existing files remain in place and supported for playback, encoding recovery, delivery and cleanup. Coordinator archives keep their existing isolated layout. No existing user files were moved or deleted.
- Offline help uses larger Segoe UI body text, bold underlined section headings, a section list, and expanded setup, gain, discovery, storage, notification and troubleshooting instructions.

## Validation

Automated results in VALIDATION-0.6.0.txt show **94 passing tests**. Existing decoder, integration, coordination, recovery and GUI tests are retained. New tests exercise persistent clearing, job uniqueness after clearing, flat audio creation, old-file retention, managed path checks, gain application, overload indication, help formatting and destination-name persistence without changing the internal ID.

The final native Windows x64 executable passed `runtime/native-final-060-check.json`: version 0.6.0, nine tabs, live gain saving without engine replacement, Dark theme, formatted help, reference/time-zone data and 69 enumerated audio devices. Synthetic reception produced two completed MP3 recordings in flat `audio/` storage and three discovered candidates. History clearing retained internal records. No external action was generated. The check used the bundled FFmpeg executable.

## Limits and remaining work

Final package: `dist/Tone-Sentry-0.6.0-Windows-x64.zip`, 62,945,328 bytes, 1,612 files. ZIP integrity, managed release-content and Windows path checks passed. SHA-256: `37d0fd77bf4fa7c35192cd3358e3fdd643330e893f28e7715078d69b8381b745`. The executable in the staged distribution folder independently passed `runtime/staged-final-060-check.json` with the same two MP3s, three candidates and zero external actions.

The current user's live receiver setup was not changed. Native Windows x64 compilation and synthetic checks do not establish field RF reliability, real-provider acceptance, other operating-system compatibility or long-duration receiver stability. The new meter and help have automated widget checks; live visual acceptance at different display scaling settings remains pending.

The development edition is unrestricted. Publisher-key provisioning, commercial license policy, legal review and complete third-party redistribution preparation remain pending. Existing source archives stay private; native compilation increases reverse-engineering effort but is not an absolute protection guarantee.

The audio-layout transition is compatibility-based: old recordings are not migrated automatically. History clearing hides records rather than reclaiming database space. Scheduler remains the audio deletion control. Receiver live-status information is not cleared as if it were a log.

Documentation update: added multiple-receiver Windows shortcut, data-folder and sound-device setup instructions to the source guide, installed help resource, HELP.md and ZIP. The executable is unchanged; ZIP integrity and matching help contents were verified. The initial ZIP was retained as a private before-update backup.
