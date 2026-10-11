# Tone Sentry 0.8.4 — delivery reliability and status

This Windows x64 test release includes all 0.8.3 features plus:

- Retry selected offers original settings or confirmed use of the currently saved destination settings. The recording and job identity stay the same; email retries keep their original recipient. Incompatible destinations and active/completed jobs are rejected.
- Recording-complete webhooks can wait for a selected FTP/FTPS destination. Choose Wait for successful FTP upload in destination settings; both destinations must use the same scope. Waiting survives restarts without consuming attempts. Failed, cancelled or missing uploads prevent the notification. Correct and retry the upload first, then the notification.
- Clear delivery statuses distinguish Waiting for FTP, Upload failed, Ready to send and Ready to retry. Double-click a delivery for details and access to the related upload, including jobs hidden from displayed history. Details omit credentials and destination URLs.
- Updated Help explains these workflows. FTP completion does not verify the public website URL or access permissions.

Close the older application before starting this build. Development remains unrestricted and unsigned. The default data folder remains %USERPROFILE%\ToneSentryData; existing settings and queued work are reused. No live receiver data is used for build diagnostics.

The user reported Microsoft Defender detecting Trojan:Win32/Ulthar.A!ml in an earlier 0.7.0 copy. The cause has not been established. This build is not claimed to resolve that detection or to have antivirus clearance. Leave protection enabled during testing and record any detection name and affected path.

Source tests cover delivery dependencies, retry recovery, UI controls and prior functionality. Package diagnostics use isolated synthetic audio and no external notifications. Live RF, remote FTP/FTPS-to-Discord acceptance and other platforms remain pending.
