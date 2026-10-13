# Tone Sentry 0.8.18 — single-file Windows test build

Copy **Tone-Sentry-0.8.18-Portable-Windows-x64.exe** to the other Windows computer and double-click it. No installer or Python installation is required. The executable contains the runtime, audio libraries, encoder, icon, tone chart, and offline help. Startup extracts the bundled runtime into a temporary folder, so the first launch may take a moment.

This build is for 64-bit Intel/AMD Windows. It is not a native ARM, Linux, or macOS executable. It is an unsigned, unrestricted development test build.

## First test on another computer

1. Start the executable from a writable local folder. Keep the supplied third-party notices with your test package.
2. A fresh computer gets its own receiver identity and settings in `%USERPROFILE%\ToneSentryData`. Settings and recordings are stored there, not inside the executable or its temporary extraction folder. If that folder already exists, its settings and queued work are reused.
3. Open Settings > Audio, detection & recording and select the sound input connected to that computer's radio. Device choices from a different machine may not apply.
4. Open Settings > Audio playback device and choose the desired speakers/headphones or System default.
5. Use Run safe demo to check synthetic detection and MP3 creation without notifications, then replay a completed recording. Use headphones to avoid audio feeding back into the monitored input.
6. Configure your real tone sets and start monitoring when ready. Manual gain is the default. Test optional Auto gain against known radio pages before relying on it.

Do not copy the original computer's whole data folder to the new receiver: that would duplicate its identity and could include credentials, queued work, and other private settings. Configure the new receiver independently. Keep its data folder outside cloud-synchronized folders.

For an isolated test that does not use an existing receiver folder, create a Windows shortcut whose Target is similar to:

```text
"C:\ToneSentryTest\Tone-Sentry-0.8.18-Portable-Windows-x64.exe" --home "C:\ToneSentryTestData"
```

Each concurrently running receiver needs its own `--home` folder and input-device selection. The in-app Help & how to guide has the full multiple-receiver setup instructions.

## Validation limits

The application source passed 231 tests (one Unix-only test skipped on Windows) for version 0.8.18. The portable artifact must additionally pass its isolated packaged diagnostic. That check uses synthetic audio, bundled MP3 encoding, GUI resources, device enumeration, and local HTTPS login/playback/control; it does not establish physical playback, radio reception, or compatibility with the second computer's audio drivers. Testing on the second machine remains necessary.

The commercial release checklist, code signing, and third-party corresponding-source distribution work remain pending. This package is for private development testing.


Default-folder migration and the compact layout are described in the included HELP.md. Close older receivers before upgrading. Existing legacy data is copied and preserved for recovery; do not use the retained copy with an older executable. Explicit --home folders are not migrated.


## Remote web access in 0.8.18

Open Settings → Remote web console on the receiver to create an account and enable
HTTPS. See docs/WEB-CONSOLE.md in this package for the address, certificate and
private-network setup. Web access is off by default. No firewall changes are made.
