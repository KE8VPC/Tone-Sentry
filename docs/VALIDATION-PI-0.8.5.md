# Raspberry Pi ARM64 test package — September 15, 2026

Artifact: `dist/Tone-Sentry-0.8.5-Pi-ARM64-Test.zip`.
Private Python source package based on the unchanged 0.8.5 application.

Verified on the Windows development host:

- 167 source tests passed, one Unix-only test skipped, two existing deprecation warnings.
- ZIP CRC and byte-for-byte content checks passed (50 files).
- Extracted application builds a Python wheel; CLI, icon, usage guide and tone
  reference PDF are present in that wheel.
- All three shell scripts pass Git Bash syntax checks.
- Dependency wheels successfully resolve/download for Linux ARM64 CPython 3.11.
  This is availability evidence, not ARM execution or validation of every Python version.
- Installer downloads dependencies separately; no runtime data, saved receiver
  configuration, credentials, Windows binaries, issuer script or virtualenv is bundled.

Not yet verified: Raspberry Pi OS apt installation, menu shortcut, Tk rendering,
USB audio capture/playback, synthetic execution on ARM, sustained reception,
external destinations and Pi 4 compatibility. No Pi hardware was available locally.
The diagnostic script operates in a fresh temporary folder and does not enable
external deliveries. The launcher explicitly uses ~/ToneSentryData.
