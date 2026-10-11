# Tone Sentry 0.8.10 development test release

## Live dispatch listening

In Settings > Audio playback device select your output, enable Play live dispatch
audio after tone detection, and Save playback device. The option is off by default.
The detected tone set must have recording enabled. Listening starts after an
accepted configured page and follows that dispatch recording until it ends,
continuing across maximum-length file splits. It does not play recording pre-roll.
Ignored or record-only scheduled tests, suppressed duplicates, discovery-only
candidates and safe demo/WAV replay do not start live output. Later stacked tones
may be audible while listening. This does not remove tones from saved MP3s.

Stop playback silences the current live session without stopping capture, recording
or uploads. The next accepted new dispatch recording can start listening again.
Playing a saved recording stops live listening and takes priority over live triggers.
Changing output settings stops playback and applies to future triggers.

Live output uses a bounded queue and converts to the output device sample rate.
Output failures appear in playback status; capture and delivery continue. Slow
output drops playback audio instead of building a backlog. Startup/buffering adds
latency and can lose initial audio if device startup is slow. Use headphones or
isolated speaker routing to prevent feedback into the monitored input.

## Interface changes

- Stop playback is beside Play recording on Overview, Recordings and Discover Tones.
- Recordings > Clear deleted hides entries already marked deleted; existing audio,
  active recordings, deliveries and internal metadata remain intact.
- About includes the requested description crediting inspiration from FD Tone Notify
  and 2 Tone Detect.

Close the previous application before opening this EXE with the same data folder.
Existing settings, recordings and filename-timezone preference are retained.
The earlier proposed start-after-tones MP3 recording option is not part of this build.
Development licensing remains unrestricted. See VALIDATION-0.8.10.txt for checks.
Physical simultaneous capture/playback and live RF remain remote acceptance checks.
