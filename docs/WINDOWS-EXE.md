# Tone Sentry 0.8.17 — Windows development build

Extract the complete Tone-Sentry-0.8.17-Windows-x64 ZIP into a folder, then open **Tone-Sentry.exe** inside it. Keep the accompanying files and folders beside the executable. This native compiled build includes Python runtime libraries, Tk, PortAudio, the tone chart, time zones, offline help and FFmpeg; no Python installation is required.

This ZIP contains the application folder. A separately named Portable ZIP contains the single-file executable. Copy or move the whole folder when relocating the program. The application is unrestricted and has no registration requirement.

Close the old application before opening Tone Sentry against the same data folder. It continues using `%USERPROFILE%\ToneSentryData`, preserving settings, agency definitions, receiver identity, recordings and destinations. Startup begins radio capture only if Start monitoring when Tone Sentry opens is enabled; but existing queued delivery jobs can resume. Do not copy a receiver data folder to another computer; each receiver needs its own identity.

## New controls

- **Shared meters:** Overview and Discover Tones have the larger gain handle, optional Auto gain, and Save meter settings. Manual is the default; dragging returns to Manual. Both tabs control the same input gain. Use the outer scrollbar to reach lists in smaller windows.
- **Playback device:** choose speakers/headphones in Settings or above the tabs. All recording playback uses this output; Stop playback is beside Play recording; playing/error feedback remains above the tabs. Radio input is unchanged.
- **Deliveries:** Clear cancelled and Clear all now join Clear completed. Pending work continues after clearing; changed statuses or attempt counts make entries reappear.
- **Overview input meter:** drag the orange gain handle, or focus the meter and use Left/Right. Green is normal, yellow begins at -12 dBFS and red at -3 dBFS. A clipping warning also detects overload already present before software gain. Gain saves automatically while monitoring continues.
- **Overview > Clear all**, **Deliveries > Clear completed**, and **Discover Tones > Clear candidates:** clear visible history without deleting audio or resetting duplicate protection. New activity still appears.
- **Destination name:** edit a readable label in destination settings. The internal ID remains stable so existing job references survive a rename.
- **Audio folder:** new local MP3/JSON files go directly into `audio/` under the receiver data directory. Existing files stay accessible in the older folder; they are not moved automatically.
- **Help & How To:** larger body text, bold underlined section titles, section navigation and detailed setup/troubleshooting instructions.

- **Settings > Appearance:** choose Light or Dark; changes save without interrupting monitoring.
- **About:** creator credit, version, help, acknowledgments and development registration status.
- **Discover Tones > Discovery settings:** enable Record discovered candidates, then adjust pre-roll, silence threshold/time, minimum duration, post-roll and maximum duration. This is off by default.
- **Discover Tones > Play recording:** replay the latest candidate clip. Candidate details includes playback for recent individual observations.
- **Scheduler:** existing automatic deletion also applies to discovery clips. Candidate measurements remain when clips are purged.

Unknown-tone clips stay local and do not trigger integrations. Normal configured-tone paging continues independently. Use headphones or avoid feeding speaker playback into the monitored radio input.

## Verification and scope

Run an isolated synthetic package diagnostic with:

```text
Tone-Sentry.exe --self-test C:/TEMP/tonesentry-check.json
```

The report directory must be writable. This mode creates temporary diagnostic data alongside the report, uses synthetic audio, checks MP3 encoding, discovery and GUI resources, and generates no external delivery. See RELEASE-STATUS.md in the development project for actual results.

This is an unsigned Windows x64 development build. Native Windows ARM64, Linux and macOS packages and live RF/provider acceptance remain pending. The new build raises the effort required to recover application logic; it does not make reverse engineering impossible. Public third-party redistribution preparation and publisher-key setup remain pending; see BUILD-AND-LIMITS.md.

For development builds, use `python scripts/build_native_windows.py` and `python scripts/package_native_windows.py`. The old PyInstaller build script and source archives are retained for private development history, not customer source protection.


Default-folder migration and the compact layout are described in the included HELP.md. Close older receivers before upgrading. Existing legacy data is copied and preserved for recovery; do not use the retained copy with an older executable. Explicit --home folders are not migrated.


## Remote web access in 0.8.17

Open Settings → Remote web console on the receiver to create an account and enable
HTTPS. See docs/WEB-CONSOLE.md in this package for the address, certificate and
private-network setup. Web access is off by default. No firewall changes are made.
