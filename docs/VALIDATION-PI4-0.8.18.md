# Raspberry Pi 4 ARM64 package validation - 0.8.18

Private test package prepared October 15, 2026. No Pi hardware or ARM execution available here.

- ZIP CRC, SHA-256 sidecar and per-file manifest verified; 69 package files.
- Installer/launcher/check scripts pass Bash syntax validation. LF endings and executable archive permissions verified.
- Packaged Python sources parse; packaged application builds an isolated py3-none-any wheel with required UI/help/audio-reference resources.
- Dependency wheels resolved/downloaded for CPython 3.11 Linux ARM64 (manylinux compatible targets). This establishes availability at packaging time, not execution on Pi or support for every Python/OS version.
- Source application remains 0.8.18, previously tested with 246 passing tests and one skip on Windows. No detector or audio-engine code changed for this package.
- Installer uses system Tk, PortAudio and FFmpeg; Python dependencies install in a private venv. No models, background services, receiver credentials or recordings included.
- Pi installer execution, actual USB audio input/output, MP3 throughput, HTTPS access and sustained reception remain user hardware tests. No deadline for field feedback.
- Transcription remains on hold. Leading-tone trimming is not implemented in this release. Google Chat live verification remains blocked by account restriction.

SHA-256: `4681448466df9c95070f09913bf7b4f4008e84bd34e1d3b38dbd0d7273febafb`
