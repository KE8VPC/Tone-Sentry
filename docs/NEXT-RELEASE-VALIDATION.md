# Delivery changes prepared for 0.8.4

## New source changes after 0.8.4: destination editor and script files

The editor now filters controls, explanatory text, previews and list editors by destination type and Discord Auto URL detection. Hidden fields are not converted or validated on save. New Script destinations use a path and Browse button; legacy argv is preserved if no file is selected. Windows .bat/.cmd uses the system batch interpreter with a quoted filename argument; Unix scripts require execute permission and a #! declaration. Arbitrary editor file associations are not used because opening an editor is not successful script execution. Timeout and exit status are still tracked; child processes are not guaranteed to terminate with their parent.

Validation: 167 passed, 1 Unix-only test skipped, 2 FTP dependency deprecation warnings (runtime/tests-destination-cleanup-final.log). Follow-up visibility tests passed after hiding fixed trigger controls. Tests include a real local batch script with spaces in its path and recording argument, nonzero exit reporting, expansion-character rejection, masked FTP test regression, Discord format/Auto switching, email/transcription/FTP/script visibility, hidden invalid numeric fields and legacy argument preservation. Linux/macOS execution remains unverified. No new EXE was built and the remote installation was not changed.

## Previous delivery changes shipped in 0.8.4

Mike requested a new build after these source changes. They are included in the 0.8.4 release; see RELEASE-0.8.4.md and its validation record for final package results. The notes below retain the source-validation history.

- Retry selected offers original settings or confirmed use of the current saved destination. It preserves job identity, event and original email recipient. Atomic queue updates reject active/completed jobs and incompatible destinations.
- Recording-complete webhooks can wait for a selected FTP/FTPS destination. Upload jobs are queued first. Waiting persists in the existing queue and does not consume attempts; a failed, cancelled or missing upload prevents notification. Matching scopes are required; no dependency is the default.
- Help and the roadmap document both workflows.

- Delivery status now describes upload dependencies and distinguishes automatic readiness from operator retry. Double-click details link to the related FTP job, including hidden history, without showing destination credentials/URLs or altering queue state.

Latest validation: **159 tests passed**, two local FTP dependency deprecation warnings (runtime/tests-delivery-status.log). Added status-transition and GUI tests verify hidden related-upload access, terminal states, privacy and read-only behavior. No new executable has been built or live provider notification sent.

The retry change passed 145 tests. The upload dependency full suite passed 151 tests (runtime/tests-upload-dependency.log). An additional GUI selector/save test then passed along with all seven dependency tests. Tests cover repeated waiting, worker restart, upload success/failure/cancellation/absence, default behavior, configuration and dropdown persistence. External handlers were simulated for dependency tests; no live notifications were sent. Earlier local FTP transport tests remain in the passing suite.

Pending: compiled-package acceptance and live FTP-to-Discord validation. Transfer completion is not proof that the public website URL is correct or publicly accessible.
