# Tone Sentry 0.8.18 — Raspberry Pi 4 test package

Private development package for Raspberry Pi OS **64-bit Desktop** on Pi 4.
Pi 5 with the same OS/architecture can also be tested. This is Python application code, not a
compiled or source-protected release. No Pi hardware validation has been completed.

## 1. Prepare the Pi

Install Raspberry Pi OS 64-bit with the desktop. Complete its normal setup,
connect to the Internet, and connect a Linux-compatible USB audio input device
to your radio. Use an appropriate audio cable/interface and a modest radio level.
Check that `uname -m` prints `aarch64`.

## 2. Extract and install

Copy the ZIP to the Pi and extract it into a permanent folder in your home
directory, for example `~/Applications`. Open a terminal in the extracted
`Tone-Sentry-0.8.18-Pi4-ARM64-Test` folder and run:

```bash
bash install.sh
bash check.sh
bash launch.sh
```

Run these as your normal desktop user. The installer requests sudo only for
OS dependencies; it installs Python dependencies into this folder's `.venv`.
Internet access is required for installation. It does not enable monitoring,
start a service, import settings, or send messages. Keep the terminal error text
if installation fails. A wheel-unavailable error means the OS/Python combination
needs investigation; the installer intentionally avoids compiling dependencies.

The application menu also contains **Tone Sentry (Pi test)**. If the menu has not
refreshed, log out/in or use `bash launch.sh`. Moving the package requires rerunning
the installer to update its shortcut. Do not move or replace it while running.

## 3. Set up reception

Data is stored in **~/ToneSentryData**, independently of the installed program.
Choose a unique site name, such as `Pi4`, and select the Pi's audio input in
Settings. Device numbers and Windows paths are not portable. Set playback output
separately. Check the input meter and gain before starting monitoring.

You can export settings from Windows and use **Settings → Import settings** on
the Pi. Review the import first. It preserves receiver-local settings/identity;
select the Pi devices yourself. Imported destinations are disabled, and exported
FTP passwords must be entered again. Review destination paths and enable each
destination you intend to test. Exported webhook URLs may contain credentials:
keep the settings file private.

For FTP/email/transcription, enable **Allow external audio / transcript sharing**
on each intended tone set. Otherwise recordings can exist locally without an
upload. For Discord file links, use `{filename_url}` in the public URL and ensure
the FTP remote filename template is blank or `{filename}`. If configured, make
the recording-complete webhook wait for the corresponding FTP upload.

Windows `.bat` files cannot run on the Pi. Use an executable shell script with
a shebang, e.g. `#!/bin/bash`, and grant execute permission with `chmod +x file.sh`.
The simplified script destination supplies the completed filename as argument 1.

## 4. Test in stages

1. `bash check.sh`: uses a fresh temporary data folder for the doctor and synthetic
   demo. Review the output for completed MP3s. It leaves that diagnostic folder
   available for inspection; it does not test RF reception or external services.
2. `bash launch.sh devices`: confirm the USB audio input is listed.
3. Open the GUI, configure reception, and check a known page and its local playback.
4. Enable intended destinations and check FTP completion, the actual remote MP3,
   Discord link playback, and the entire recorded dispatch.
5. Restart the application and verify saved configuration/device selection.
6. Monitor overnight for audio errors, CPU/temperature problems, missing deliveries,
   recording cutoffs and excessive duration. Overlapping transmissions remain
   best effort; do not expect recovery of audio obscured over the radio.

Avoid running Windows and Pi against the same destinations during the initial
test unless you want both to deliver. Unique receiver identities and filenames
do not alone suppress redundant notifications; receiver coordination is separate.

## Troubleshooting and removal

For a launch failure, run `bash launch.sh` in a terminal and retain the error.
For no inputs, inspect Raspberry Pi OS audio settings and the USB connection.
For no GUI, use a desktop login; this package does not install a remote GUI or
automatic startup service. Do not launch the receiver as root.

Close Tone Sentry before rerunning the installer. It preserves `~/ToneSentryData`.
To remove this test installation, close the application, delete its extracted
program folder, and remove `~/.local/share/applications/tone-sentry-pi-test.desktop`
(or the corresponding XDG_DATA_HOME location). Keep the data folder for recovery.

See `app/tonepage/resources/usage-guide.md` for the full guide and
`app/tonepage/resources/third-party.md` for dependency acknowledgments. Dependencies
are downloaded by the installer, not bundled here. This package is for private
testing; commercial redistribution preparation remains separate.


## Features and boundaries in this package

This package uses the 0.8.18 application source, including discovery overlap labels,
notify-only beeps, and the optional HTTPS web console. Python 3.10 or newer is
required. A 32-bit OS is not supported by this installer, even on a 64-bit Pi.
No model/LLM is installed. Transcription development is on hold; leading pager-tone
trimming is not implemented in this version. Google Chat remains available but
live validation is blocked by the account restriction reported by the user.

For beeps, open Playback device, select a Pi output, choose Notify only, set
volume, and Preview alert tone. Discovery beeps are a separate checkbox. Existing
recording and delivery settings are independent. Confirm actual speaker routing
on the Pi; Linux output device names will differ from Windows.

For remote web access, keep the desktop application open, use Settings > Remote
web console, and create a local account. Use listen address 0.0.0.0 for private-LAN
access, set the browser address to the Pi's LAN IP, and save. Open the displayed
HTTPS URL on another computer and compare the certificate fingerprint before
accepting its warning. See docs/WEB-CONSOLE.md. No firewall/router changes or
background service are installed. The command-line headless receiver does not
provide the embedded desktop web console in this release.

This installer does not require a clean OS or reformatting. On an existing Pi,
stop any old Tone Sentry instance before installing/upgrading. Keep an independent
backup of ~/ToneSentryData. Do not copy a Windows receiver's entire data directory
onto the Pi. Use the settings export/import workflow above instead.

Hardware performance is unmeasured: check dropped audio blocks and temperature
under your actual monitoring/discovery workload. Start with a single receiver
instance. The package does not alter CPU clocks, power management, or OS audio
configuration. You can retain this ZIP and test later; there is no reporting
deadline or activation requirement. Internet package availability can change
between packaging and installation. Save terminal output if installation fails.
