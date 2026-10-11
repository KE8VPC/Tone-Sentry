# Review of supplied weekly-test recording

Analyzed October 1, 2026. Original MP3 preserved unchanged (SHA256
f287e046cf414b80b1887060315b677d7a7c0bb5ae31088b5ba9972d48627c59).
Duration 58.70 seconds. Analysis uses a local mono 16 kHz PCM working copy.
Frequencies and timings are approximate measurements, not confirmed standard tone
assignments. No speech transcription or agency-order identification was performed.

| Start in file | End | Type | A / long Hz | B Hz | A duration | B duration |
|---|---|---|---|---|---|---|
| 3.48 s | 7.48 s | Two tone | 770.17 | 1699.31 | 1.00 s | 3.00 s |
| 9.96 s | 18.96 s | Long tone | 2050.23 | — | 9.00 s | — |
| 21.48 s | 25.48 s | Two tone | 638.01 | 653.09 | 1.00 s | 3.00 s |
| 27.96 s | 36.96 s | Long tone | 1615.24 | — | 9.00 s | — |
| 39.48 s | 43.48 s | Two tone | 1123.37 | 1286.23 | 1.00 s | 3.00 s |

The first second of the file contains approximately 1520.6 Hz already present at
the start. Its beginning is unavailable; this fragment cannot establish a full
page duration or whether it belonged to an A/B pair. The complete page groups
above are separated by about 2.5 seconds, with no substantial A/B gap inside the
measured pairs.

## What explains the discovery difficulty

- The old discovery code rejects neighboring tones whose separation is at most
  twice the stability tolerance. At the default 8 Hz tolerance, the measured
  15.08 Hz separation between 638.01 and 653.09 is rejected. Stability and distinct
  A/B frequency separation are different questions; the source fix separates them.
- A recurring approximately 136.5 Hz component exists between pages. The operator confirmed
  136.5 Hz is the paging channel CTCSS tone. Treating it as a paging tone can join separate pages
  into misleading candidate stacks. A configurable lower frequency bound of 250 Hz
  excludes it in this sample; this bound must be reviewed for other paging systems.
- The original defaults fragment the 1699 Hz tone (1.72 s measured instead of
  approximately 3 s) and the 2050 Hz tone (6.6 s instead of approximately 9 s).
  Duration drafts based on those fragments could be misleading.

The archived detector/discovery code from the preserved 0.8.5 Pi source package
produces four candidates on this working copy. The revised source with the settings
below produces the five groups listed above. This comparison concerns discovery,
not proof that the live configured-tone detector missed the same pages.

## Discovery settings used for the revised comparison

- Frequency range: 250–3500 Hz
- Stable run minimum: 0.4 seconds; long-tone minimum: 2 seconds
- Stable run maximum: 15 seconds
- Maximum inter-tone gap: 0.8 seconds
- Stability allowance: 12 Hz
- Minimum purity: 0.75
- Missing-frame bridge: 0.12 seconds
- Shared input analysis: 16 kHz working copy, 40 ms frames, default minimum RMS

These are sample-tested starting values, not a universal calibration. The 12 Hz
stability setting remains below the close pair's separation. Lower purity and
bridging can admit false candidates, so compare repeated clean pages and voice
identification. Do not assign agencies using their order in the MP3 filename.

The review ZIP contains a CSV and five tone-only clips with short surrounding
margins. They are listening aids, not notification-ready agency recordings.
The original MP3 and receiver configuration have not been changed. Discovery changes are included in the 0.8.8 development release; see its validation notes.
