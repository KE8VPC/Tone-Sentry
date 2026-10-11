# Tone Sentry 0.8.7 development test release

Most configuration changes can now be saved while monitoring continues.

- Destination settings apply to future jobs. Already queued and running deliveries
  retain their saved destination settings; saving never retries or cancels them.
- Tone, detector, discovery and recording settings wait for a quiet processing
  boundary with no active page sequence, normal recording or discovery recording.
  The status line reports pending changes. Continuous traffic can defer application;
  another save replaces the pending configuration. Saved changes survive restart.
- Input device, channel or sample-rate changes close and reopen the audio stream
  automatically at that boundary, after captured blocks drain. Monitoring remains
  enabled, but reopening causes a brief reception gap. A page during that gap can
  be missed. An unavailable new input reports the specific error and retries;
  choose the previous working input to recover. No automatic device substitution.
- Active recordings retain their MP3 encoder and filename settings. Background
  encoding continues while configuration changes are applied.
- Replay keeps its detector settings until replay finishes; pending settings apply
  afterward. Live gain controls remain available.

Receiver coordination/identity changes and full settings import still require
stopping monitoring. Those operations have broader identity/queue implications.
The separate coordinator service still needs a restart for its own settings.
Changing destinations does not retroactively upload previously skipped recordings.

Native stream reconfiguration is covered with a simulated input in source tests;
actual USB driver reopening, RF reception and provider delivery require field checks.
No remote receiver configuration was changed during development. Development
licensing remains unrestricted. Pi 0.8.5 test package is unchanged.
