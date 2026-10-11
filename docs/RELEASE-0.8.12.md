# Tone Sentry 0.8.12 development test release

Completed recordings are now checked against disk at startup and when Recordings >
Clear deleted is clicked. If a managed MP3 was deleted outside Tone Sentry, its
recording entry becomes deleted and can be cleared from the visible list.
The check supports audio/ and the older recordings/ folder structure. It does not
delete any files, cancel deliveries or remove internal recording metadata.
Active and encoding recordings are skipped. Permission and other access errors
are not taken as proof of deletion. A missing JSON sidecar alone does not mark an
existing MP3 deleted. Missing files outside managed folders are not classified.

Clear deleted scans before clearing, so restarting is unnecessary for that action.
There is no continuous folder watcher. A renamed or moved MP3 counts as absent at
its original path; this release does not automatically relink restored files.
Pending deliveries of manually deleted files can still report a missing-file error.

The About narrative now describes the operational beta, limited support and operator
responsibility, as requested. All 0.8.11 features remain available. Close the old
application before opening this build with the same data folder. If monitoring on
startup is enabled, the saved input will open automatically. See VALIDATION-0.8.12.txt.
