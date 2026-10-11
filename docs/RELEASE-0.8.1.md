# Tone Sentry 0.8.1 — FTP password entry

The destination editor now has a normal masked **FTP password** field. Enter the actual password, test the connection and save the destination. Both FTP and FTPS use this password for connection tests and recording uploads. Stop monitoring before saving settings, then enable the destination and resume monitoring when ready.

Passwords are stored in the configuration as Base64, at the user's request. This is reversible encoding, not encryption. Anyone with access to the data folder or its backups can recover them. Settings exports omit these saved FTP passwords; enter them again on the receiving computer. Other existing export contents, such as webhook URLs, have not changed.

An unchanged empty password box preserves the saved password. Entering a replacement updates it. Typing and then erasing the value saves an empty password. Legacy password environment-variable settings continue to work when no saved Base64 password exists; entering a new password replaces that legacy reference. The application does not interpret an old environment-variable name as a literal password.

Connection testing uses the current form values without saving. It checks login and directory access, not upload permissions. Local tests cover actual plain FTP uploads and retries, encoded-password login, masked form editing, export omission and malformed values. Remote DreamHost FTP/FTPS and live radio delivery require operator testing.

Existing delivery jobs retain the destination settings captured when they were queued. Test a newly recorded page after saving the password; retrying an older failed job does not replace its old credential reference. Encoded passwords can also be present in the local delivery database and its backups.

This unrestricted Windows x64 test release includes the 0.8.0 interface, recording and data-folder changes. The default data folder remains %USERPROFILE%\ToneSentryData. Close the older application before using this version.
