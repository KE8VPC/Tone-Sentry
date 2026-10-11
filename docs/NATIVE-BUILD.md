# Tone Sentry 0.8.0 — native development build

This is an unrestricted private development build. Detection, recording and existing integrations do not require registration. The Windows default is ToneSentryData; the legacy default is copied and preserved for recovery when safe. Explicit data folders remain unchanged. See the packaged help for migration details.

## Compilation

Build with Windows x64 Python 3.10.11, the application and encoder dependencies, Nuitka 4.2.1, ordered-set and zstandard:

```text
python scripts/build_native_windows.py
python scripts/package_native_windows.py
```

For the separate single-file Windows test build, retain the matching standalone package's notices, then run:

```text
python scripts/build_native_windows.py --onefile
python scripts/package_portable_windows.py
```

The portable executable extracts its bundled runtime to a temporary directory when launched. Receiver settings remain in the normal persistent data folder. See [portable testing instructions](PORTABLE-TESTING.md).

Nuitka compiles the Tone Sentry application modules to native code. This increases the effort needed to recover logic compared with the former PyInstaller bytecode bundle. It does not make reverse engineering impossible. Strings, resource files, public license-verification keys and configuration formats remain inspectable. No signing secret is embedded.

The native compiler cache uses a short path under the Windows user profile to avoid MinGW header path-length failures in packaged desktop hosts. The build downloads Nuitka's supported MinGW compiler when needed. Build outputs and compiler caches are development-only.

The staged bundle is inspected for application Python source/bytecode, debug symbols, private-key files, runtime databases, tests and build scripts. Do not publish the development source or the old source ZIPs as a customer release. Those archives are retained privately and cannot be made secret retroactively.

References: [Nuitka user manual](https://nuitka.net/user-documentation/user-manual.html) and [standalone-first build guidance](https://nuitka.net/user-documentation/tutorial-setup-and-build.html).

## Third-party distribution work before a public release

This private development package includes FFmpeg 7.1 essentials from imageio-ffmpeg. Its own version output identifies the Gyan build with GPL and version-3 options. Exact version/configuration and license output are saved in third-party-notices, alongside installed Python dependency licenses.

Before distributing a customer/public release, prepare and verify corresponding source/build materials for this exact FFmpeg binary and its linked dependencies, or replace it with a separately built encoder whose matching source is maintained alongside the release. An upstream link alone has not been verified as a complete corresponding-source delivery. Tone Sentry application source and third-party dependency source are separate release concerns.

Upstream references: [Gyan builds and source links](https://www.gyan.dev/ffmpeg/builds/), [FFmpeg 7.1 source](https://github.com/FFmpeg/FFmpeg/tree/n7.1), [FFmpeg legal information](https://ffmpeg.org/legal.html). No public upload or customer distribution was performed.

## Registration foundation

About contains offline signed-key verification, masked key entry, persistent activation storage and an explicit unrestricted-development status. The trusted public-key list is intentionally empty until Mike provisions a publisher signing identity. The activation button is disabled in this build. No expiry, device count, transfer rule, trial or free/full restriction has been invented.

The private `scripts/license_issuer.py` utility creates an encrypted Ed25519 private key and public verification key, then issues signed full-edition keys. Keep the private key outside this repository, OneDrive and customer packages; keep its passphrase separately. Do not lose either. Provision a public key before building an activation-enabled release. Example publisher workflow (paths must be chosen deliberately):

```text
python scripts/license_issuer.py init --private-key C:/PRIVATE/publisher.pem --public-keys tonepage/resources/license-public-keys.json --key-id publisher1
python scripts/license_issuer.py issue --private-key C:/PRIVATE/publisher.pem --key-id publisher1 --licensed-to "Receiver owner" --output C:/PRIVATE/receiver-registration.txt
```

The utility asks for the passphrase interactively; it does not print private keys. Public verification keys are packaged; issuer scripts and private keys are not. Activation is saved separately as registration.key in the data folder and excluded from routine settings exports. Existing recordings and identity survive invalid activation attempts.

## Remaining acceptance

Native binary self-test and local UI checks do not establish live RF detection reliability, provider account delivery, long-duration receiver stability, resistance against an actual reverse-engineering attempt, or Linux/macOS/ARM operation. Code signing remains pending. Windows native dialogs follow OS appearance. Other display scaling settings and File Explorer/taskbar icon behavior need separate visual checks.
