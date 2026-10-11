Tone Sentry 0.8.5 overnight script test

1. Copy ToneSentry-Overnight-Test.bat to a writable folder on the test PC,
   for example C:\ToneSentryScripts. Avoid quotes, percent signs and exclamation
   marks in the folder name. Spaces are supported.
2. Stop monitoring before changing settings.
3. Add or edit a Script destination. Browse to this BAT file in Script file.
   No arguments or interpreter settings are needed in 0.8.5.
4. Select Local scope, enable the destination and select only Recording complete.
   Leave agency filters unchecked for all configured agencies, or select the
   agencies you want. Use a 10-second timeout.
5. Save and resume monitoring. If replacing the old log script, disable its old
   destination or edit it instead of leaving both destinations enabled.

The file creates a logs folder beside itself and appends to:
C:\ToneSentryScripts\logs\ToneSentry-overnight.log
(The actual location follows the folder where you put the BAT file.)

Each receipt contains the local computer's date/time, computer name and the MP3
filename received from Tone Sentry. Time is the script execution time, not the
initial page time. The date format follows Windows regional settings.

Double-clicking the BAT manually writes a NO_FILENAME entry. That checks folder
write access only. During a recording-complete delivery, expect a RECORDING entry
with the MP3 filename. No window remains open and the script needs no input.

The script exits with code 0 after a successful append, or 1 if it cannot create
the log directory or append to the log. It does not move, delete, upload, open or
inspect recordings and does not verify their contents, FTP success or Discord
links. It requires no administrator privileges when its folder is writable.

Tomorrow compare the receipts with Recordings and Deliveries. A missing entry may
mean no matching event was queued, a disabled destination/filter, or a script
failure. A repeated receipt can be caused by a manual/automatic retry; this log
does not deduplicate jobs. No entries during a quiet period are expected.

Run safe demo does not send destination actions, so it will not create a script
receipt. Use normal monitored pages for the overnight end-to-end test.
