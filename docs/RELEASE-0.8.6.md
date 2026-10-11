# Tone Sentry 0.8.6 development test release

- Audio input choices identify their PortAudio interface without hiding matching
  device names or changing the saved device index.
- Audio settings include a read-only, copyable diagnostic report: selected input,
  saved channel/sample rate, device inventory, default rates and last capture error.
  Opening diagnostics does not test/open a stream. It does not automatically refresh
  PortAudio after a USB reconnect. Restart the application if the inventory is stale.
- Capture-error event details preserve the actual error and attempted settings.
- Deliveries shows queued local date/time, recording filenames when available,
  horizontal scrolling, and an explicit Details button.
- Destination setup identifies enabled tone sets whose external-sharing permission
  is off and provides a review list. It never enables sharing automatically.
  New sharing-blocked events explain why a delivery was skipped.
- The header includes Created by: Mike Beam, wrapping below the title on tight layouts.

Monitoring still must be stopped for general configuration changes. This release
does not implement live settings updates or change detection timing/frequencies.
Already queued deliveries retain their saved settings. Old generic audio-error
events cannot acquire missing error details retroactively.

The user's four-agency live test demonstrated detection, recording, FTP and Discord
audio links after enabling sharing. Other agencies require frequency/timing review.
Overlapping dispatch traffic remains best effort. These reports do not establish
universal hardware compatibility. Pi package 0.8.5 remains a separate test artifact.
