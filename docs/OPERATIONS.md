# Receiver operation

## Input and detection

Connect the radio to a line input or USB audio interface. Select the correct device, sample rate and zero-based channel in Settings. Gain scales input before detection. The level meter measures relative audio RMS, not calibrated RF strength.

The default is mono 16 kHz with 40 ms detector frames. The detector removes DC, estimates the strongest spectral peak with interpolation, and requires sufficient energy concentrated around it. Each A/B sequence is evaluated independently, with frequency, duration and inter-tone gap limits. Long tones have minimum and maximum durations.

Recognition occurs when the final tone ends, allowing maximum-duration rejection. Set pre-roll longer than the expected complete tone sequence if you want all tones included. An 8-second buffer can preserve a typical 5-second long tone but cannot preserve an arbitrarily long tone from its start.

Close frequencies and noisy radio audio require calibration. Imported 1697/1699 Hz values have overlapping tolerance bands; their different A tones distinguish the sequences. No operational accuracy percentage has been established.

Device loss retries every three seconds. Queue overflow or substantial timestamp gaps log audio-gap events, reset tone state and finish an active recording as interrupted. Closing the GUI stops reception; use headless `run` under a service manager for unattended operation.

## Recording controls

| Setting | Behavior |
|---|---|
| `pre_roll` | Buffered audio before recognition |
| `post_roll` | Minimum time after the last tone before closing |
| `silence_seconds` | Continuous below-threshold audio needed to close |
| `silence_rms` | Audio threshold for silence |
| `min_seconds` | Minimum duration after recognition in silence mode |
| `fixed_seconds` | Fixed duration after recognition; zero selects silence mode |
| `max_seconds` | Maximum duration per part; prolonged traffic creates linked parts |
| `stack_seconds` | Window for adding agency activations to an active recording |
| `retention_days` | Days after completion before cleanup; zero disables deletion |

Audio writes incrementally to a managed WAV spool. A separate worker produces MP3 using FFmpeg/libmp3lame and removes the WAV only after successful finalization and job scheduling. Failed encoding retains WAV. Restart recovery can resume interrupted capture files, but power loss can still lose buffered samples or damage a source; lossless crash recovery is not promised.

Starting a new recording requires at least 100 MiB free disk space. This is a guard, not an unlimited-storage guarantee. Monitor available space and the event log.

## Repeats and test windows

Duplicate suppression is per configured tone ID and persists across restarts. The interval is anchored to the first accepted activation. Repeats suppress external actions while continuing or creating a follow-up recording. A different incident using the same tones inside the interval cannot reliably be distinguished from a re-page.

Add weekly schedules in **Scheduler > Add weekly test**. Select an agency, weekday checkboxes, start hour/minute, duration, time zone and ignore/record-only mode. Edit or remove rules from this tab. Automatic deletion and its age are also configured here.

Monday is 0; Sunday is 6. `ignore` logs without independently starting a recording; `record_only` records without external actions. Ignored tones within an active recording remain in its metadata and sharing restrictions. Both occurrences of a fall-back hour match; a nonexistent spring-forward interval has no matching local timestamps. A real page inside the window follows the same exclusion rule.

## Storage and retention

Filename tokens: `{date}`, `{time}`, `{offset}`, `{agency}`, `{agencies}`, `{site}`, `{instance}`, `{session}`. Filename times are UTC; UI timestamps use the local timezone. Unsafe characters are replaced. A full recording UUID is always appended.

Every instance owns its SQLite database, queue and `recordings/<instance UUID>/`. Keep runtime data outside OneDrive, Dropbox and shared writable directories. Source code may be shared; live state may not.

Cleanup first runs after one minute of background operation, then approximately hourly. Only completed tracked files inside the managed root qualify. Pending, failed and ambiguous jobs protect their recordings by default. Retry or explicitly cancel those jobs; retention may exceed the configured age until resolved. Cancelling releases protection. Automatic age-based deletion of transcripts and event metadata is not implemented yet.

## Replay and settings

Replay accepts 16-bit PCM WAV at the configured sample rate and channel. Replay/demo records are marked synthetic and cannot create external actions or outbound coordination jobs. Their duplicate state is separate from live reception. Previously queued live jobs may still run in the background.

Edit settings while reception is stopped and background jobs are idle. Dedicated forms cover tones, audio/detection/recording, schedules, integrations, receiver connection and coordinator enrollment. No JSON editing is needed for these settings. Queued jobs retain their destination snapshot: editing or disabling a destination does not cancel existing jobs. Use Deliveries to cancel them.

The OS releases the process lock at exit; deleting the lock file is not a valid way to bypass another process. An external operation may be in flight during shutdown. Transfers/webhooks can retry; scripts with interrupted outcomes are marked ambiguous for review because they may already have produced effects.

