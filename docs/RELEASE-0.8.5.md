# Tone Sentry 0.8.5 — simpler destination setup

- Destination fields, help, preview buttons and recipient/provider/header editors now follow the selected destination type. Discord controls appear only for Discord format or a recognized Discord URL in Auto mode. Unsaved values survive switching types, while saving includes only applicable settings.
- Script destinations now use a Script file entry and Browse button. Windows supports .bat/.cmd; Linux/macOS scripts require executable permission and a #! interpreter declaration. The MP3 basename is passed automatically as argument one. No manual interpreter or argument rows are needed.
- Existing command-and-argument destinations remain unchanged until a replacement file is selected. Choosing or saving a file does not execute it. Script exit status and timeout remain tracked; child processes are not guaranteed to stop with their parent.
- Help describes the new editor and script workflow. Windows paths/filename arguments containing quotes, percent signs, exclamation marks or line breaks are rejected rather than expanded by the batch interpreter.

Close the older application before launching. This is an unsigned, unrestricted Windows x64 development build using the existing ToneSentryData folder. No remote installation is automatically updated.

The user reported script setup problems and an unresolved MP3-upload or Discord-link issue during remote testing. This release packages the editor changes; it does not claim to fix or diagnose those delivery issues. Further script/field testing is deferred until the user resumes it. A newer build reportedly did not trigger Defender, but the older 0.7.0 alert has not been conclusively explained.

Source tests include real local batch execution, spaces in paths/arguments, failure reporting, destination visibility and legacy command preservation. Packaged checks are isolated and synthetic, not proof of live RF/provider reliability or Linux/macOS compatibility.
