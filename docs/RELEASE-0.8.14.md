# Tone Sentry 0.8.14 development test release

Overview now matches the compact Discover Tones layout:
- Each summary box shows its label and value on one line, with reduced padding.
- The boxes use one row where space permits and two rows on narrow/scaled displays.
- The VU/gain meter occupies the left half; Reset gain, Auto gain and Save meter
  sit to its right. Gain caption and clipping feedback remain visible.
- Removed the introductory paragraph and separate Input level row, and reduced
  spacing above the playback controls and activity table.

No detection, recording, playback or delivery behavior changes. Layout bounds and
single-line card contents checked at 1100x740 and 880x460 with Tk scaling 1.33 and
2.0. Actual remote display/DPI remains a field check. Close the old application
before opening this build against the same data folder. Startup monitoring may
start automatically if enabled. See VALIDATION-0.8.14.txt for package evidence.
