# Discover Tones: capture, review and split

Discovery workflow for the 0.8.8 development release.

1. Select the known working receiver input. Open Discovery settings, optionally
   fill the weekly-test starting values, review them, then Save. This enables
   discovery and local audio capture only; no alerts are enabled. Capture must
   be active before the test. Pending changes wait for a safe boundary.
2. Watch live peak/purity and the short-run, overlong-run and low-purity counters.
   They reset with the detector and are clues, not proof of a particular problem.
   A low signal below the common minimum RMS gate still cannot be discovered.
3. Select a candidate and open Review sequence / split stacked pages. Select an
   observation and play its full original recording. Use dispatch voice and known
   test order to identify agencies. Existing frequency matches do not prove identity
   or timing correctness; uncheck Hide frequencies already represented when needed.
4. The sequence table lists measured frequencies, durations and gaps. Select two
   neighboring runs (Ctrl-click) for an A/B draft, or one run for a long-tone draft.
   A–B–C–D may mean A/B plus C/D; B/C is an overlapping alternative, not a confirmed
   agency. A single 3-second run could also be a B tone whose A tone was missed.
5. Create each draft separately, review the suggested timing, enter the agency,
   and save. The draft starts disabled with external sharing off. Confirm multiple
   clean observations before enabling alerts. Splitting creates tone definitions,
   not new or destructive edits to the source MP3.

The weekly-test values are adjustable starting points, not a calibrated preset:
minimum run .4 s, long tone 2 s, maximum run 15 s, inter-tone gap .8 s, variation
12 Hz, purity .75, dropout bridge .12 s, frequency range 250–3500 Hz. Audio limits remain operator-controlled;
silence stopping must exceed the inter-tone gap. Lower purity can admit speech.

Discovery now receives frequency estimates before the configured detector's purity
filter; configured-page detection retains its own threshold. The shared RMS gate
and frame size remain unchanged. A short missing/low-purity segment can be bridged
only if the same frequency returns; another tone is never bridged across. The
default bridge is .08 s and can be disabled. Reported bridged duration includes the
short hole; listen before trusting the timing. Separate transmitters simultaneously
on one channel cannot be reliably untangled by a single-peak tracker.

Full sequence timing is saved for new observations. Older observations without
gap measurements must be captured/analyzed again before pair splitting. Partial
recordings cannot recover omitted tones. WAV analysis still uses the stopped
receiver's replay workflow and requires the configured sample rate/16-bit PCM.
Further work: more field samples and isolated offline analysis while live reception continues.

The supplied weekly-test MP3 was analyzed locally: five complete page groups were recovered with these starting values. See WEEKLY-TEST-REVIEW-2026-10-01.md. The original code missed the close 638/653 Hz pair and fragmented two durations. The adjusted lower frequency bound excludes the operator-confirmed 136.5 Hz channel CTCSS tone in that sample. Agency assignments remain unconfirmed.
