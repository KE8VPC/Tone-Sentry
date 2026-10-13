# Tone Sentry

A portable Python radio-paging receiver with a desktop console and headless mode. Detect two-tone sequential and long single-tone pages, record MP3 dispatches, and coordinate redundant receivers.

**Version 0.8.18 is an unrestricted development build.** Current features include the remote HTTPS web console, Google Chat and Discord notifications, FTP/FTPS delivery, and local tone discovery. Tone Sentry is standalone; integrations with other applications and services are optional. See [release notes](docs/RELEASE-0.8.18.md), [validation status](docs/RELEASE-STATUS.md), and [Google Chat setup](docs/GOOGLE-CHAT.md).

This private repository contains source, tests, documentation and application assets. Receiver settings, credentials, recordings, runtime data and compiled build packages are excluded.

## Standalone Windows executable

The native Windows x64 bundle is `dist/Tone-Sentry-0.8.18-Windows-x64.zip`. Extract the whole folder and open Tone-Sentry.exe; retain its companion files. Python runtime libraries and FFmpeg are included. See [Windows instructions](docs/WINDOWS-EXE.md) and [compilation/redistribution limits](docs/NATIVE-BUILD.md).

## Start on this Windows computer

After installing the development dependencies, open **`launch_windows.cmd`** to launch the console. New receiver data defaults to `%USERPROFILE%\ToneSentryData`. The example legacy tone library can be previewed and imported; cloning this repository does not configure a live receiver automatically.

1. Open **Settings → Audio, detection & recording** and select the receiver sound input and channel.
2. Review **Tone library**, including imported minimum durations, proposed maximum durations, and frequency tolerances.
3. Use **Run safe demo** or **Replay WAV** to exercise detection and MP3 output without sending notifications or running scripts.
4. Click **Start monitoring** to capture live input. Settings that require a safe boundary are applied when capture permits; follow the status shown in the application.
5. Use **Settings → Destinations & actions** for optional destinations. They remain disabled until explicitly enabled. Credential handling depends on the destination; follow its setup guide. Never commit local credentials or receiver settings.

Monitoring on startup is optional and disabled by default. Keep receiver runtime data outside synchronized source folders. A second launch against an active data directory displays an error instead of opening the database concurrently.

## Install on another computer

Use Python 3.10 or newer. One source ZIP or Python wheel is shared across operating systems; the runtime and native audio/encoder dependencies must match the target machine.

**Windows:** install Python with Tk support, extract the ZIP, run `setup_windows.cmd`, then `launch_windows.cmd`. The encoder extra supplies an FFmpeg binary where a supported wheel exists.

**Linux / Linux ARM:** install Python, venv support, Tk, PortAudio and FFmpeg with the distribution's package manager. Run `sh setup.sh`, then `sh launch.sh`. Debian-derived systems commonly provide `python3-venv`, `python3-tk`, `libportaudio2`, and `ffmpeg`. ARM can use system FFmpeg without a bundled encoder wheel.

**macOS:** install a compatible Python distribution with Tk, PortAudio and FFmpeg, then use the same shell setup/launcher. Headless reception does not require a desktop display.

For manual setup, create and activate a virtual environment, then run `python -m pip install .`. The optional `.[encoder]` extra provides an FFmpeg binary on supported platforms.

## Commands

```text
python -m tonepage gui
python -m tonepage devices
python -m tonepage doctor
python -m tonepage run
python -m tonepage demo
python -m tonepage replay dispatch.wav
python -m tonepage status
python -m tonepage import-other tones.cfg
python -m tonepage import-other tones.cfg --apply
python -m tonepage --home /absolute/coordinator-data coordinator
```

`--home` precedes the command and selects a separate data directory. Defaults: Windows `%USERPROFILE%\ToneSentryData`; Linux/macOS `$XDG_DATA_HOME/tone-page-detect` or `~/.local/share/tone-page-detect`. First launch migrates the legacy Windows default when safe; see the offline help for backup and recovery behavior.

The sanitized library is included as [examples/auglaize-tones.cfg](examples/auglaize-tones.cfg). Preview/apply it with `import-other` on another receiver. Fresh installations get their own UUID; run `new-identity` after cloning settings onto a different receiver.

## Features

- Continuous input capture, level display, clipping detection, reconnection attempts, and audio-gap events.
- Duration-validated two-tone and long-tone detection with an editable agency library.
- MP3 pre-roll, silence/fixed ending, stacked agency associations, continuation parts, and JSON sidecars.
- Persistent duplicate-action suppression and timezone-aware weekly-test windows.
- Safe filenames, FTP/explicit FTPS, durable retries and protected retention cleanup.
- Discord-compatible outgoing webhooks, SMTP MP3 email, a configurable multipart transcription adapter, and opt-in scripts.
- Authenticated receiver coordination, heartbeat roster, shared events, isolated source recordings, preferred audio, and centrally queued actions.
- Other application import preview for TwoToneDetect and FD Tone Notify, configuration export, diagnostics, and safe replay.
- Searchable offline tone reference, dedicated Scheduler tab, form-based settings and in-app Help (F1).

## Documentation

- [Next-release roadmap: About, dark theme, branding and source protection](docs/ROADMAP.md)

Open **Help & how to** in the main window or press **F1**. The [usage guide](tonepage/resources/usage-guide.md) is bundled offline, along with the supplied tone chart.

FD Tone Notify imports start disabled pending timing review. One/two-frequency sequences are supported; longer sequences are reported and skipped.

- [Configuration and recording behavior](docs/OPERATIONS.md)
- [APIs, credentials and scripts](docs/INTEGRATIONS.md)
- [Redundant receivers](docs/COORDINATION.md)
- [Legacy import details](docs/IMPORT-REPORT.md)
- [Verified behavior and remaining limits](docs/RELEASE-STATUS.md)
- [Original requirements and longer-term design](REQUIREMENTS.md)

## Development and packaging

```text
python -m pip install ".[encoder,test]"
python -m pytest -q
python -m build
python scripts/package_release.py
```

The old `dist/TonePageDetect-0.4.1-portable.zip` is a **private development source archive**, retained for history. Do not ship it as a protected customer release. The 0.5.0 binary bundle excludes application source, bytecode, tests, private issuer scripts and runtime data. Native compilation does not establish live radio or cross-platform acceptance.

## Unknown-tone discovery

Open **Discover Tones** and use **Start discovery** for your selected radio input, or **Analyze WAV** for an offline recording. Enable **Record discovered candidates** in Discovery settings to retain local audio with silence-based stopping. **Play recording** replays the latest clip, and **Candidate details** includes playback for recent observations. Review measured frequencies, durations and ambiguous stacks before creating a disabled tone-set draft. See the in-app Help guide for limits and settings.
