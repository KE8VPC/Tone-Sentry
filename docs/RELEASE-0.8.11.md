# Tone Sentry 0.8.11 development test release

Settings now includes Start monitoring when Tone Sentry opens. The checkbox saves
automatically and applies on the next normal GUI launch. It uses this receiver's
saved audio input, tone sets and delivery settings. Default is off, including for
older configurations. Enabling it does not start capture immediately.

Auto-start is scheduled after the interface is initialized. It never toggles an
already-running receiver off. The normal input error/retry behavior applies if the
saved device is unavailable. Stop monitoring remains available. Closing the app
cancels a pending startup action. Settings import preserves this receiver-local
preference. Diagnostic, demo and WAV replay commands do not auto-start live capture.

This starts monitoring when the application opens; it does not register the app
with Windows Startup or start it when the computer boots. Existing 0.8.10 features,
including optional live dispatch playback, are retained. Close the older app before
opening this build with the same data folder. Development remains unrestricted.
See VALIDATION-0.8.11.txt for test/package results. Physical input startup on the
remote machine remains a field check.
