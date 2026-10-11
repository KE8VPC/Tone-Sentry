# Tone Sentry 0.8.13 development test release

Discover Tones uses a compact top section:
- Half-width signal/gain meter with Reset gain, Auto gain and Save meter on its right.
- Shorter workflow guidance and reduced spacing.
- Removed the Since last detector reset counter line; capture audio on/off and
  pending-settings feedback remain in the main status line.
- Review stacked is inline with playback, draft, details, export and clear actions.
- Shorter button labels and automatic wrapping on narrower windows.
- Hide-known-tones and clear-history feedback share a row; the long footer note is
  removed from this page. Detailed guidance remains in Help and Discovery settings.

Discovery, detection, gain processing, recordings and deliveries are unchanged.
Window geometry checked at 1100x740 and 880x460 with two Tk scaling settings; button
bounds and the approximately half-width meter were verified. Hardware display/DPI
acceptance remains a field check. Close the old app before opening this build with
the same data folder. Startup monitoring may start if enabled in your settings.
See VALIDATION-0.8.13.txt for package checks.
