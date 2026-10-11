# Tone Sentry 0.8.8 development test release

Discover Tones now supports reviewing measured sequences and selecting individual
long tones or neighboring A/B runs from stacked pages. Recent observations retain
run durations and gaps. Each proposed agency starts disabled with sharing off.
Older observations without gap measurements require recapture before pair splitting.

- Fixed rejection of distinct close-frequency pairs, including the measured 638/653 Hz pair.
- Discovery has its own purity threshold, configurable short dropout bridging,
  frequency limits and counters to help explain rejected or fragmented runs.
- Discovery settings offers reviewable weekly-test starting values. Click the
  starting-values button, review, then Save; existing installations are not changed automatically.
- The 250 Hz lower bound in those starting values excludes the supplied channel's
  operator-confirmed 136.5 Hz CTCSS from candidate discovery. Recorded audio and
  configured agency frequencies are unchanged.
- A supplied 58.70-second recording produced five complete page groups using these
  settings. Agency identities remain unknown; filename order is not identification.

Start in Discover Tones > Discovery settings. After capturing, select a candidate,
open Review sequence / split stacked pages, listen, and select one run for a long
tone or Ctrl-click two adjacent runs for an A/B draft. Review timings and identify
an agency before enabling it. A/B/C/D may be A/B plus C/D; B/C is only an alternative.
The source recording is preserved; splitting creates drafts, not separate MP3 files.

Lower purity may admit speech. These values are sample-tested starting points,
not universal calibration. Simultaneous transmitters remain a limitation. WAV replay
still requires stopped monitoring and matching-rate 16-bit PCM. Discovery uses the
shared input RMS gate. Quiet-boundary live settings behavior from 0.8.7 is retained.

Development licensing remains unrestricted. Windows x64 package checks are recorded
in VALIDATION-0.8.8.txt. Live receiver acceptance and the next weekly test remain
field checks. The Pi 0.8.5 test package is unchanged.
