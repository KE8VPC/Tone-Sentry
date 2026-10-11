# Tone Sentry 0.7.0 — unrestricted development release

## Changes

- Larger orange gain handle, shared tricolor meters on Overview and Discover Tones, Auto gain checkbox, and Save meter settings with feedback. Manual remains the default. Dragging returns to Manual. Gain is applied once to reception; changing controls does not replace the engine.
- Conservative automatic gain increases only during sustained tone-like input, holds during silence/noise, and reduces promptly on overload. Range is 0.10x–8x; manual range stays 0.01x–100x. Hardware clipping still requires reducing the upstream input.
- Deliveries adds Clear cancelled and Clear all beside Clear completed. Clearing persists across restart without cancelling work or deleting recordings. Hidden unfinished jobs reappear when their status or attempt count changes.
- Playback now runs inside the application with a saved output-device selection, refresh, stop control, and playing/error feedback. Overview, Recordings and discovery observations use the same player. Radio input remains independent.
- Settings uses compact rows. Overview and Discover Tones scroll vertically to keep their controls and lists reachable in smaller windows. Offline help explains the new controls and retains the separate-folder/shortcut instructions for multiple receivers on one computer.

## Validation and limits

The source test suite passed 104 tests on Windows x64. Layout checks at 1240×820 and 1020×690 confirmed the Overview and discovery lists remain reachable after the scroll correction.

The native 0.7.0 executable passed its isolated diagnostic: two completed MP3 recordings, three discovered candidates, 69 enumerated audio entries including 38 output entries, shared meter persistence/override, bundled resources and formatted help. No external deliveries were sent and no live input or physical playback was opened.

Automated checks cover existing detector/integration behavior, synthetic gain transitions, shared controls and persistence, mixed delivery states across restart, output identity changes, and real FFmpeg decoding into a simulated output stream. No physical speaker output or radio capture is performed by those checks. The packaged diagnostic uses isolated synthetic reception, bundled MP3 encoding, GUI dialogs, tone resources, and device enumeration without external notifications.

Actual output-device switching, disconnection during playback, simultaneous live RF reception, AGC performance on dispatch traffic, and display scaling still need operator acceptance. Software playback cannot prevent feedback through speakers, microphones or operating-system loopback routing. Windows x64 is the supplied artifact; Linux, macOS and ARM builds are not validated by this release.

The development edition stays unrestricted. Registration policy, publisher signing, and the commercial-release third-party source/licensing checklist remain pending. Existing data folders and previous recordings remain compatible. Keep the complete extracted release folder together; do not replace files inside a running older version.
