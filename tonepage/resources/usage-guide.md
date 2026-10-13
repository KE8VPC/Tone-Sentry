TONE SENTRY — GETTING STARTED

Tone Sentry listens to a selected audio input for paging tones. A configured tone set identifies an agency; Discover Tones measures possible new tone sets for you to review. Neither a strong meter reading nor a discovered frequency alone confirms a real agency page.

1. Follow First setup to select the radio input and verify your tone sets.
2. Run safe demo or Replay WAV to check local detection and recording without notifications.
3. Review Shared meters and auto gain, then confirm known pages from your radio.
4. Choose playback speakers/headphones and listen to a completed recording.
5. Set up schedules and destinations when local reception works. Monitor delivery results separately from recording success.

Use the section list to jump to the detailed steps. The compact header contains Help, Safe demo, Replay WAV, Start/Stop monitoring and Playback device in one row. On narrow windows their labels shorten to Help, Safe demo, Replay, Start/Stop radio and Output. The tagline is beneath the program name; receiver and playback status share a small row below. The minimum window size is 880x460; scroll longer pages to reach all controls and lists.


INSTALLATION AND DATA FOLDERS

The Windows default data folder is %USERPROFILE%\ToneSentryData. The single-file portable executable includes its runtime and extracts it to a temporary folder during startup; persistent settings and recordings remain in the data folder. The folder-style package must be extracted with all companion files. Neither requires an installed Python runtime.

Close the older receiver before starting this version. If only the old TonePageDetectData folder exists, first launch copies it into ToneSentryData, updates internal recording paths, and preserves the receiver identity and delivery state. The original folder is retained for recovery and marked as an old migration copy. Copying a large audio collection may take time and requires enough free disk space for both copies. Do not run an older executable against that retained copy: its delivery state becomes outdated. While the new default receiver runs, it locks the retained legacy folder as well.

If both folders already exist independently, the application stops and asks you to select the intended folder with --home. It does not merge them. An interrupted copy remains in a ToneSentryData.migrating-* folder and is never opened as the receiver; a later launch can retry from the original. If a completed migrated folder is lost, restore the current backup rather than resuming stale jobs from the original. Keep regular backups of settings AND the data folder. A settings export alone does not contain audio or queued-job history.

Explicit --home paths are preserved and are not automatically migrated. Use a fresh, separate data folder for another computer or receiver; do not clone a receiver identity. See Multiple receivers on one computer for Windows shortcut examples.


FIRST SETUP

1. Open Settings → Audio, detection & recording. Select the radio-connected input device and channel (0 is the first channel). Choose a sample rate, start with gain 1, and save.
2. Open Tone library. Add an agency or choose Import other application. Edit each agency’s frequencies, timing, duplicate window and enabled checkbox.
3. Use Run safe demo or Replay WAV to check detection and MP3 recording. Replay needs 16-bit PCM WAV at the configured sample rate. These modes never send external actions.
4. Connect the radio and select Start monitoring. Watch the input level and events. Most settings can be saved while monitoring; check the status line for pending changes. Input changes cause a brief automatic reconnection. Confirm real radio detections and audio before operational use.

SHARED METERS AND AUTO GAIN

Overview and Discover Tones have an outer vertical scrollbar for smaller windows. Scroll down to their history lists; the list's own scrollbar moves through its entries. You can also use the mouse wheel over the controls or Page Up/Page Down after focusing the outer page.

Overview and Discover Tones show the same receiver input and gain. The larger orange handle adjusts the shared gain once, before detection and recording. Drag it or use Left/Right arrows to return to Manual mode. Reset gain returns to Manual at 1.00x.

Manual gain remains the default. Select Auto gain to allow bounded adjustments from 0.10x to 8.00x. Upward adjustment requires a sustained tone-like signal above a minimum level; gain holds during silence and ordinary noise. Excessive levels reduce gain promptly. The applied gain is shown beside both meters. This conservative tone-assisted control is not a general speech loudness normalizer and still needs verification with your radio. It cannot recover audio already clipped upstream.

Use Save meter settings on either tab for immediate saving and the Saved feedback. Drag changes also save automatically after a short pause. Mode and manual reference gain are remembered per receiver folder. Automatic gain's moment-to-moment value is not continuously written to disk. Unchecking Auto during reception keeps the current applied gain as the manual setting. Monitoring and recording continue while changing these controls.

The slim meter measures input sample peaks after gain. Green extends to -12 dBFS, yellow to -3 dBFS and red to full scale. The white marker shows measured peak; the orange vertical handle controls gain. Red means little headroom remains; CLIPPING also flags input already clipped before software gain. Reduce radio or sound-device volume if necessary: software gain cannot restore a clipped waveform. Manual gain ranges from 0.01x to 100x. Click anywhere on the meter or focus it and use Left/Right arrows to adjust.


TONE REFERENCE

Tone library → Tone reference opens the supplied CE45 2-Tone Code Chart offline. Search by group, tone number, chart code or Hz. In a tone editor, Select from tone reference fills the associated A / long or B frequency. Choose both frequencies independently. Chart codes are reference-table indexes, not agency identifiers. Undefined entries cannot be selected. Open original reference PDF displays the supplied sheet in your PDF reader.
For a single long tone select long; B fields are unused. For two-tone sequential paging select two. Minimum and maximum durations are seconds, not match counts. Detection completes when the final tone ends. Percentage tolerance applies independently to each frequency; uncheck it to use absolute Hz. Avoid overlapping A/B tolerance bands.

IMPORT OTHER APPLICATION

The file picker accepts TwoToneDetect CFG/INI and FD Tone Notify JSON configurations. The preview lists proposed agencies and warnings. Apply replaces the tone library; export a backup first. Original files are unchanged. Existing destinations with agency filters are disabled when their referenced tones are replaced. Imported agencies have external audio sharing off.
TwoToneDetect: imports A/B or long-tone frequencies, minimum lengths, descriptions and repeat suppression. Proposed upper timing limits and tolerances need review.
FD Tone Notify: imports compatible one- and two-frequency detectors, percentage tolerances, lockout periods, recording enable flags, supported sample rates, recording duration overrides and purge age. Sequences longer than two tones are skipped and listed. All imported detectors start disabled: matchThreshold counts pitch estimates and cannot be faithfully converted to seconds. Confirm A/B or long-tone timing, then enable each agency. Reset timeout, clarity, audio scaling and device names are not equivalent to this engine’s controls. Source notifications, credentials, executable commands and output paths are not copied.
The FD Tone Notify format is documented at https://github.com/kjdElectronics/fd-tone-notify and its config/default.json. Native Tone Sentry backups are distinct from other-application imports.

RECORDING, STACKED PAGES & DUPLICATES

Pre-roll preserves audio before a detection. Minimum duration, post-roll and silence determine when a recording closes; fixed duration selects a timed mode. Maximum part duration splits long traffic into continuation files. For stacked agencies, the longest participating recording limits apply. Per-agency duration overrides are available in its tone editor. A disabled Record detected pages checkbox prevents that agency from starting a recording; an existing recording can still contain the radio audio.
Stacked agencies share an active recording within the stack window. Repeat suppression prevents repeated alert actions, while detections remain visible and repeat audio may still be recorded. Choose the repeat window carefully: a second real call inside that window can be suppressed.
Filenames use {date}, {time}, {agency}, {agencies}, {site}, {instance}, {session}, {offset}. Filename date/time uses the selected Local time or UTC setting and describes recording start. New local filenames append a six-character random ID. File reservation checks prevent collisions, and the matching JSON uses the same stem. Existing filenames are preserved. Internal recording UUIDs stay unchanged; including {session} or {instance} in a custom filename will still include those full IDs by choice. MP3 encoding requires FFmpeg; the optional encoder package supplies it on supported systems, or select a local executable. Pending encoding retains the source WAV.

DISCOVER TONES

Open Discover Tones. Select the radio audio input in Settings first. Start discovery enables candidate tracking and starts the existing receiver audio input. If monitoring is already running, discovery changes apply at the next quiet boundary. Use Stop monitoring to stop reception. Discovery settings has an Enable checkbox and controls for minimum stable-tone duration, minimum long-tone duration, maximum duration, maximum tone-to-tone gap, allowed frequency variation and spectral purity.
Analyze WAV runs safe offline analysis using the existing replay path: 16-bit PCM WAV at the configured input sample rate and channel. Replay measurements are labeled separately from live measurements. Enable discovery before using the main safe demo to see example candidates. Uncheck Hide frequencies already represented in my tone library to see known/example frequencies. This filter compares frequencies and paging format, not timing or agency identity; disabled library entries also count as represented.
Each row shows the last observation, measured A/B or long frequency, duration, spectral purity, observation count and live/replay source. Double-click or choose Candidate details for measurement JSON, up to 20 recent timing observations and the three closest entries in the supplied reference chart. Chart matches are suggestions only; measurements are not snapped to chart frequencies. Repeated frequency pairs within approximately 8 Hz are grouped, so very close real tone sets can share a candidate row. The latest 1,000 candidate groups persist across restarts; older groups are removed as new groups arrive. Export candidates saves all retained groups as JSON.
Create tone-set draft opens the regular editor with measured frequencies and proposed timing tolerances. Enter the correct agency name before saving, and confirm timing against repeated observations and actual radio audio. Drafts start disabled and cloud sharing is off. Saving a draft does not enable alerts. You must explicitly enable it after review.
Two-tone discovery looks for consecutive stable tones; single long tones must be isolated by the configured gap. More than two consecutive tones produces overlapping adjacent pairs flagged Stack / ambiguous. For A-B-C-D, possible rows are A/B, B/C and C/D; the program does not know which pair boundaries belong to agencies. Replay that ends during a stable tone is flagged End cut off. These are advisory observations, not confirmed page detections. Music, signaling carriers and some speech can resemble paging tones. Spectral purity is a signal measurement, not a probability or identification confidence.
The common input gain, minimum signal and analysis frame settings also apply. Discovery cannot bypass the main tone analyzer's purity floor. Gaps or dropped audio reset discovery state instead of combining disconnected fragments. No agency name can be inferred reliably from frequencies alone.

RECORDING UNKNOWN TONES

In Discovery settings, enable Record discovered candidates. This is off by default. Set the audio pre-roll, continuous silence time, silence RMS threshold, minimum capture duration, post-roll and maximum total clip duration. Silence time must exceed the allowed tone-to-tone gap. Lower RMS thresholds treat quieter input as activity; increase the threshold if receiver noise prevents silence stopping. A maximum-length clip stops even with an open carrier, then waits for silence before rearming.
Capture starts provisionally when a stable tone reaches the minimum discovery duration. A pre-roll buffer preserves the first tone. Activity that never becomes a valid candidate can still leave an Unknown tone activity clip in Recordings. Stacked candidates share a clip. Normal configured-tone recording uses its own recorder and limits.
Choose Play recording on Discover Tones for the latest observation. Candidate details also opens a recent-observations list with playback for individual captures. Audio states distinguish Recording, Encoding, Ready, Missing and Purged. Scheduler retention includes these clips; measurements remain after audio deletion. Discovery clips stay local: they never trigger uploads, notifications, scripts, transcription or coordinator publication. Playback uses the same selected output as Overview and Recordings; use headphones and avoid routing playback into the monitored input.

If recording never stops, inspect receiver noise during a quiet period. Adjust the silence RMS threshold or the radio's squelch, and choose enough continuous silence to bridge normal pauses. The maximum clip duration always limits a discovery recording; after reaching it, discovery capture waits for silence before rearming. Normal configured-page recording uses its own limits.

PLAYBACK AND JSON DETAILS

Select an event in Overview or a file in Recordings, then use Play recording. Audio plays inside Tone Sentry through the selected playback output. Use Stop playback next to Play recording on Overview, Recordings, or Discover Tones to stop it. Playback does not submit samples directly to the detector; speakers or loopback routing can still feed audio into the monitored input. The information icon opens the selected event/recording JSON in a popup. Events without finished audio cannot be played, including purged files.

CHOOSING PLAYBACK SPEAKERS OR HEADPHONES

1. Open Settings > Audio playback device, or Playback device above the tabs.
2. Choose System default to follow the operating system output, or select a named output. Host audio system and current device number help distinguish entries. The saved choice uses the device name and host audio system, since numbers can change after reconnecting equipment.
3. Click Save playback device. This stops any current playback and changes future playback without changing radio input or restarting monitoring.
4. Select a completed recording in Overview, Recordings, or Discover Tones and click Play recording. Candidate details also supports individual captured observations. The bar above the tabs shows opening, playing, finished, or error status. Click Stop playback to stop.
5. If an output is disconnected, click Refresh devices and select another available output. An unavailable or ambiguously named saved output produces an error rather than silently playing elsewhere. Reconnect it and refresh, or choose System default. If two outputs have identical names on the same host audio system, give them distinct operating-system names or choose another host entry.

Each receiver data folder remembers its own playback choice. Speakers near a microphone, stereo mix, virtual cables, or loopback routing may cause replayed pages to be detected again. Choose headphones and check the operating-system routing. Playback device selection alone cannot prevent acoustic or system-level feedback.

AUDIO FILES AND HISTORY CONTROLS

New local recordings and their matching JSON information files are stored directly in the audio folder under your receiver data directory. There is no instance-ID subfolder for new local clips. Open recording folder opens this location. Older files stay in the previous recordings folder so existing playback links and queued deliveries continue to work; they are not automatically moved. Receiver identity remains in metadata. Coordinator archives retain separate receiver storage for isolation.

Overview > Clear all hides existing activity entries; new activity continues to appear. Deliveries > Clear completed hides successful jobs. Clear cancelled hides cancelled jobs. Clear all hides every current delivery entry after confirmation; pending/running work continues. Hidden unfinished deliveries reappear when their status or attempt count changes. These actions do not cancel or retry deliveries. Discover Tones > Clear candidates hides existing candidates; a new observation can make a candidate appear again. These controls preserve audio files, settings and internal duplicate protection. Hidden entries remain hidden across restarts. Use Scheduler retention to delete old audio files; clearing a log does not delete audio.

SCHEDULER

Open Scheduler → Add weekly test. Select individual tone checkboxes or Select all tones, then weekdays, 24-hour start time, duration and time zone. Choose ignore to suppress the test or record_only to keep audio without alerting. Uncheck Enable weekly window to pause the rule. Saving creates a rule for each selected tone and avoids identical duplicate rules. These are independent rules; later-added tones are not automatically included. Windows may cross midnight; named time zones follow daylight saving changes. Rules apply by detection start time. An ignored agency already present in an active stacked recording can remain in its metadata/audio.
Automatic cleanup is configured only on Scheduler. Check Automatically delete recordings older than, enter whole days and save. Unchecked disables automatic deletion. The background worker periodically deletes eligible tracked recordings; unfinished deliveries protect files, including failed jobs awaiting retry or cancellation. Cleanup does not recursively delete arbitrary files or delete remote FTP copies.

DESTINATIONS & ACTIONS

Settings → Destinations & actions → Add destination. Choose webhook, email, ftp, ftps, transcription or script. Destinations begin disabled. Select shared or local scope, triggers and agency checkboxes. All unchecked agencies means every agency. Save validates the configuration. Only relevant fields for the selected destination type are used.
Webhook: enter URL; optionally specify bearer-token, signing-key and HTTP-header environment-variable names. Select tone detected, recording complete and/or transcript complete. Remote HTTP endpoints require HTTPS. Idempotency keys allow receivers to suppress retries.
FTP / FTPS: enter host, port, username, remote directory and your actual password in the masked FTP password box. Test the connection, enable the destination and save. FTPS uses explicit TLS. Select only Recording complete. Transfers use temporary remote filenames before final rename.

FTP passwords are saved as Base64 in the configuration, not encrypted. Settings exports omit these saved passwords; enter them again on the other computer. Data-folder backups still contain them. Leaving the password box unchanged preserves an existing password. Enter a new value to replace it. Existing password environment-variable configurations remain supported until you enter a password directly. A connection test checks login and directory access only; it does not verify permission to upload recordings.
Transcription: configure a provider accepting multipart audio uploads and a JSON text result. Enter endpoint, bearer-token environment name, audio form-field name (often file), response text field (often text), and daily submission limit. Add provider fields such as model using the name/value controls. Select only Recording complete. This is a generic adapter, not universal provider compatibility. Provider credentials and any charges are managed with that service. To forward transcripts, configure a webhook on Transcript complete with Include transcript checked.
Scripts: select Script, then enter a Script file path or click Browse. Windows supports .bat/.cmd files; Linux/macOS scripts need execute permission and a #! interpreter declaration. The completed MP3 filename is passed as the first argument automatically (%1 in a batch file, $1 in a shell script); earlier triggers receive an empty filename. Set the timeout and relevant triggers, then save. Selecting or saving a file does not run it. The script runs from its own folder. Script errors and timeouts can leave effects uncertain; inspect before retrying. A timeout stops the process being monitored, but does not guarantee every child process it started has stopped.

Existing executable-and-argument destinations remain unchanged when the Script file field is left empty. Selecting a file replaces that legacy command on save. New file selection uses Windows' batch interpreter or the Unix script's declared interpreter, not a document/editor association, so completion and exit status can be tracked. On Windows, script paths and filename arguments cannot contain quotes, percent signs, exclamation marks or line breaks. No interpreter switches or manual argument rows are needed for the simplified setup.

Destination settings show only controls and help relevant to the current type. Discord previews and templates appear for Discord format, or Auto when a Discord URL is recognized; generic webhook, FTP, email and transcription options appear only where applicable. Switching types preserves unsaved entries while the form stays open. Saving keeps the settings for the selected type; hidden fields do not block validation. Recording-only destinations automatically use Recording complete.
Password-reference fields are masked on screen; masking is not storage encryption. Credentials: enter environment-variable NAMES in these forms, not secret values. Set their values in the operating-system environment before launching the application. Audio/transcript sharing also requires Allow external audio / transcript sharing on all participating agencies. Review Deliveries for results, retries and cancellation.

SHARED FILENAME AND MESSAGE TEMPLATES

The {filename} placeholder is the final MP3 basename, including .mp3, with no local folder path. It is available for Recording complete and related Transcript complete events; before a recording is complete it is empty. It uses the actual finalized name, including collision handling. Full internal recording IDs remain available through {recording_id}.

In destination settings, optional templates can customize generic webhook messages, email subjects/bodies, and FTP remote filenames. Leave an optional template blank to preserve previous behavior. Generic webhooks add rendered text in the message field of their event JSON and include filename metadata. Email subject templates replace the normal subject prefix plus agency; body templates replace the standard body. Email still attaches the MP3. FTP filename templates change only the remote basename, uploading directly into the configured FTP remote directory without receiver or recording subfolders. Do not use slashes or traversal in remote filenames.

Common message placeholders are {agency}, {agencies}, {date}, {time}, {site}, {event_type}, {event_id}, {recording_id}, {filename}, and {filename_url}. Webhook {transcript} is available only with Include transcript and sharing permission; email templates do not include transcript text. Use Preview optional templates to inspect sample output without sending. New deliveries use saved templates; queued deliveries keep their saved destination settings.

Examples: email subject {agency} - {filename}; email body File: {filename}; FTP remote filename {filename}; generic webhook message {site}: {filename}. Script arguments support {filename} alongside existing scalar event placeholders such as {path}; add each argument separately. Adding filename text does not attach audio to a webhook, and a filename is not a public download URL.


DISCORD WEBHOOKS

Set destination type webhook. The message format dropdown offers auto, generic or discord. Auto detects official Discord webhook URLs, including destinations saved by older versions. Discord messages show agency names followed by local event time, for example Wapak FD/EMS - 2:05 PM; transcript text is included only when explicitly enabled and sharing is permitted. Mentions are disabled. Discord delivery is text-only; it does not attach the MP3. Use the complete channel webhook URL. Discord uses the token embedded in its webhook URL; generic webhook credentials are hidden for Discord. Forum/media channels need an existing thread_id query parameter.
The older generic event JSON can cause Discord HTTP 400 because it lacks Discord message fields. After upgrading, use Deliveries > Retry selected for a failed job you want to send. Do not retry messages that already arrived. Discord does not guarantee deduplication from the generic Idempotency-Key header. If the error occurs inside Discord while creating the webhook, rather than during application delivery, it needs separate diagnosis.

CUSTOM DISCORD MESSAGE FORMAT

Open Settings > Destinations & actions, select the webhook and choose Edit selected. The Discord message template defaults to {agency} - {time}. Available placeholders are {agency}, {agencies}, {date}, {time}, {site}, {event_type}, {event_id}, {recording_id}, {filename}, {filename_url}, and {transcript}. Agency and agencies both list all participating agencies separated by commas. The date and time use the sending computer local time zone. Use Preview Discord message for a sample without sending anything, then Save destination while monitoring is stopped. Invalid placeholders are rejected. Templates affect Discord formatting only, not generic webhook JSON. Use {{ and }} for literal braces.
To show only agency and time, keep the default template and leave Include transcript unchecked. When transcript inclusion is enabled, use {transcript} to position it; otherwise it is appended. Existing queued deliveries retain their saved destination settings; new detections use your saved template. Changing this field does not enable MP3 uploads to Discord.

EMAIL WITH MP3 ATTACHMENTS

Settings > Destinations & actions > Add destination: choose email. Enter the SMTP server, port, encryption, username, password environment-variable name, sender address, subject prefix and maximum attachment size. STARTTLS normally uses port 587; implicit TLS uses port 465. Follow your mail provider's settings. Authentication supports SMTP username/password or app passwords; OAuth-only SMTP accounts are not supported. An anonymous trusted relay can leave username blank, but TLS is still required.
Add recipients individually using the list controls. Select Recording complete only. Choose agency filters and enable the destination; enable external audio sharing for each participating agency. Each recipient receives a separate email containing the MP3, without exposing the other recipients. Sender, recipient, subject and server settings are validated before saving. The configured attachment limit applies before MIME encoding; base64 and message headers add overhead against your provider's total-message limit.
Email jobs use the durable retry queue and protect the recording while pending. Temporary failures retry; permanent SMTP failures require review in Deliveries. Stable Message-ID values help identify retries but cannot guarantee exactly-once delivery after an uncertain server response. No email is sent by safe demo/replay. Live account delivery must be verified with your own SMTP provider.

EXPORTING AND IMPORTING SETTINGS

Use Settings > Export settings to save a transferable JSON settings file. Saved Base64 FTP passwords are omitted. Other destination details, including webhook URLs, may still be private.

To import, stop monitoring and choose Settings > Import settings. Select a Tone Sentry export. Review the tone counts, destination counts and changed sections, then choose Apply import or Cancel. Tone sets, weekly test schedules, detection/discovery settings and destination lists replace their current counterparts. Cancel leaves settings unchanged. Invalid or unsupported files are rejected.

This receiver keeps its identity, site name, audio input and gain, playback output, theme, encoder path, automatic deletion policy and receiver/coordinator connection settings. This avoids copying another machine's device bindings or starting a new deletion policy. Review these local options separately after an import. The existing Import other application option in Tone library is still used for legacy tone files.

Imported destinations are disabled, and saved FTP passwords are not imported. Review endpoints, script paths and environment-variable references, enter FTP passwords, and enable destinations individually when ready. Import does not send a test notification or run an imported script. Existing queued jobs retain their previous destination settings.

Before applying, Tone Sentry saves a complete local settings backup in the data folder's backups directory. These backups can contain credentials. If applying fails, it restores the previous configuration; if runtime recovery also fails, close and reopen the app. Recordings and history are not part of a settings import. The local backup is a full config snapshot; importing it through this interface still uses the same receiver-preservation and disabled-destination rules.

WAITING FOR AN UPLOAD BEFORE POSTING A LINK

Delivery status now distinguishes Queued, Uploading, Waiting for FTP, Upload failed, Upload cancelled, Upload not queued, Ready to send, Ready to retry and Completed. Ready to send proceeds automatically; Ready to retry means the upload has recovered but you must retry the failed notification. These labels describe the queue without changing its processing state.

Double-click a delivery to open its readable details, or choose View delivery details / related upload from the Retry selected menu. For dependent webhooks, Open related upload shows the FTP job even if it was cleared from the displayed history. Opening details does not restore cleared history, retry work or send anything. Use Refresh details for a current snapshot. Destination credentials and URLs are not shown in this view.

Create and save your FTP or FTPS destination first. Then edit the Discord or generic webhook destination and choose it in Wait for successful FTP upload. Select only the Recording complete trigger, use the same Delivery scope for both destinations, and enable both. The FTP tone filter must include each tone whose webhook depends on it, and those recordings must allow sharing. Save the destination settings before testing a new recording.

The notification waits for the selected upload to finish successfully. Waiting is shown in Deliveries and does not consume retry attempts. Restarting Tone Sentry preserves the wait. If the upload fails, is cancelled or was never queued, the notification fails with an explanation instead of posting an unavailable link. Correct and retry the upload first, then retry the notification. This confirms the FTP transfer completed; it does not test your website's public URL or access permissions.

Choose Do not wait to keep independent delivery. Existing queued notifications keep the settings they were created with; use Retry selected > Use currently saved destination settings to apply corrected settings to an eligible job.

RETRYING A FAILED DELIVERY

After correcting a destination, save it first. In Deliveries, select the failed job and open Retry selected. Use original delivery settings repeats the queued job with its original settings. Use currently saved destination settings opens a confirmation and replaces that job's destination settings with the current saved values, including credentials, server and message template. Unsaved edits are not included.

The recording and delivery ID stay unchanged. An email retry keeps only its original recipient, and that recipient must still be configured. Removed, disabled or incompatible destinations cannot be used, nor can active or completed jobs. A script retry can repeat effects if its previous outcome was uncertain. Existing automatically scheduled retries continue using the original snapshot until you explicitly choose saved settings.

TESTING AN FTP DESTINATION

Open Settings > Destinations & actions and edit or add an FTP or FTPS destination. Enter the host, port, username, FTP password and remote directory, then click Test FTP connection. The test uses the current form values even before saving, and does not enable or save the destination. Leave the password environment-variable field empty when entering a password directly.

The test connects, logs in, enters the configured remote directory and asks the server for its current directory. FTPS uses certificate verification. A successful result confirms login and directory access only: no files or folders are created, and upload permission or the data-transfer connection is not tested. The directory must already exist for this check, although a normal delivery may create missing directories. Failures identify the stage to check without displaying passwords or raw server replies. If you edit fields during the test, run it again to test the changed values. Save destination separately when ready.

MULTIPLE RECEIVERS ON ONE COMPUTER

You can run more than one Tone Sentry window on the same computer, with each monitoring a different sound device. Each receiver must use its own data folder. You can use the same executable and application folder for every receiver.

1. Choose separate data folders outside OneDrive or other synchronized folders. For example, use C:/Users/YourName/ToneSentry-Fire and C:/Users/YourName/ToneSentry-EMS. Replace YourName with your Windows account name. Tone Sentry creates each folder and its default settings when that receiver is first launched.

2. Create a Windows shortcut to Tone-Sentry.exe for each receiver. Right-click each shortcut, open Properties, and edit Target. Keep the full executable path in quotation marks and place --home and gui AFTER the closing quotation mark. The --home argument must come before gui. Use your actual executable location; these examples assume the application folder is C:/Apps/Tone-Sentry:

Fire shortcut Target:
"C:/Apps/Tone-Sentry/Tone-Sentry.exe" --home "C:/Users/YourName/ToneSentry-Fire" gui

EMS shortcut Target:
"C:/Apps/Tone-Sentry/Tone-Sentry.exe" --home "C:/Users/YourName/ToneSentry-EMS" gui

3. Rename the shortcuts so you can tell them apart, such as Tone Sentry - Fire and Tone Sentry - EMS. Launch each shortcut. Each window now has independent settings, recordings, delivery jobs and receiver identity.

4. In each window, open Settings > Audio, detection & recording. Select the specific sound device connected to that radio rather than leaving it on the system default. Choose the correct input channel and give the receiver a recognizable name. Save, configure its tone sets and destinations, and select Start monitoring.

5. Confirm that each window responds to its intended radio. Check its meter, make a local recording, and verify the audio before enabling live notifications. The Fire receiver's new recordings go into ToneSentry-Fire/audio; the EMS receiver's go into ToneSentry-EMS/audio. Both MP3 files and their accompanying JSON information files are kept there.

If the second window reports that another instance is already using the data directory, check both shortcut Targets. Double-clicking the executable twice without separate --home arguments selects the same default ToneSentryData folder, and the second instance is blocked to protect the files. Use fresh data folders; do not copy a running receiver's database or duplicate its receiver identity to create another receiver. Import tone definitions or configure the new receiver separately.

Each independent receiver has its own duplicate-page history. If two receivers hear the same pages and notify the same destination, configure the optional coordinator for that coverage group to help suppress duplicate notifications. Radios monitoring unrelated channels should use appropriate separate coverage groups when coordinated. Sharing an executable does not automatically coordinate the receivers.

If one input will not open, check its selected device/channel and whether another application or the audio driver is reserving the device. Simultaneous reception depends on the sound devices and drivers; test both inputs together on the actual computer. The application's separate-folder and per-device support does not by itself prove a particular hardware combination works.

REDUNDANT RECEIVERS

Each receiver needs its own data folder and unique instance ID. Do not share a live SQLite database, recording folder or copied identity between computers. Receivers retain independent local recordings and upload observations to a trusted coordinator. Configure the same tone IDs, receiver group and coverage identifier for receivers monitoring the same paging system. Different coverage identifiers separate unrelated channels.
Receivers → Configure receiver connection sets coordinator URL and token environment name. Settings > Coordinator administration provides listener and enrollment-list forms. TLS deployment and the command-line coordinator service are described in docs/COORDINATION.md included in the test package. This is an administrator setup step. During outages local reception continues; shared delivery waits for the coordinator. Receiver status shows last-known peer health. Matching pages are correlated and a recording candidate is chosen after the collection window; audio is not mixed together.

APPEARANCE AND ABOUT

Settings > Appearance offers Light and Dark. The choice is remembered and can be changed while monitoring without restarting the receiver. Application forms, help, tables and JSON views follow the selected theme. Native operating-system title bars, file pickers and message boxes follow Windows/macOS/Linux appearance settings.
About displays Tone Sentry, its version and Created By:  Mike Beam, plus help and third-party acknowledgments.

REGISTRATION — DEVELOPMENT EDITION

This development release is unrestricted. All current features remain available offline without a registration key. Offline signed-key verification is included, but publisher signing-key provisioning and free/full policies are still pending. The activation button remains disabled until an authorized publisher public key is included in a build. Activation records are separate from settings exports. No activation failure stops reception or deletes recordings.

TROUBLESHOOTING

No meter movement: check the radio cable, selected input, selected channel and whether the radio is producing audio. Confirm the operating system allows the application to use that input. Avoid choosing an output device when an input is required.

Signal present but no page detected: check that the agency is enabled and that its two-tone order, frequency tolerance and timing match the received tones. Review weak audio, clipping, weekly ignore windows and repeat suppression. Use Discover Tones as an aid, then verify against a known page rather than enabling every candidate.

No playable recording: look at the recording status. Wait for Encoding to complete. Purged means Scheduler retention removed it; Missing means the expected file is unavailable. Encoding errors preserve the original WAV for recovery. Check free disk space and the configured FFmpeg path.

Notification failed: open Deliveries and read Last result. Check the destination's enabled state, agency filter, event trigger and required audio-sharing permission. Confirm the provider URL/server and the environment variable holding credentials. Retry only after correcting the cause. Retrying an ambiguous script can repeat an external action. Cancel selected stops further attempts and releases that job's retention protection; it does not retract a message already accepted by a provider.

Duplicate notifications: review the agency duplicate interval, overlapping definitions and receiver coordination. Clear all does not reset duplicate protection. Two separate data directories represent independent receivers; coordinate them deliberately rather than sharing or copying a live database.

Missed/false detection: confirm reference frequencies, timing, tolerance, minimum level and purity using actual radio recordings. A reference chart does not identify which tones your department uses.

Cannot save: stop capture/replay and allow active background jobs to finish. Correct the specific validation message; invalid changes are not saved.

Files not purged: verify Scheduler is enabled and that pending/failed jobs are resolved. Purge runs periodically while workers run.

Use Export settings for a backup. Windows default data is in your user profile’s ToneSentryData folder. Keep configuration and recordings backed up separately. Do not clone receiver identity when setting up another machine.

RELEASE VALIDATION

One shared Python codebase targets Windows, Linux, macOS and ARM. Native audio and encoder dependencies must be available for the target platform. Local validation was performed on Windows; other operating systems and actual radio hardware require field validation. This application has not been certified as an emergency alerting system.

RECORDING DOWNLOAD LINKS

New local MP3 filenames replace whitespace with underscores. Existing recordings keep their original names. {filename} always returns the exact basename; {filename_url} URL-encodes it for a link, preserving underscores and encoding spaces as %20. Use the exact placeholder spelling with no spaces inside braces.

Discord example: [Listen to recording](https://example.com/audio/{filename_url}). Replace the example address with the public address that serves your configured FTP folder. Keep the FTP remote filename template blank (or {filename}) so the uploaded name matches the notification. Custom remote filename templates must be reflected in your link template. FTP directory paths and public website URLs are not necessarily identical. The file becomes available only after the FTP upload finishes. Select Wait for successful FTP upload on the webhook to post after that transfer completes; with Do not wait, the jobs can finish in either order.

FTP uploads no longer append instance/recording folders. Existing remote files are not moved. Retries verify existing bytes before acknowledging a matching file; different content causes a collision error instead of overwriting it. Verification requires remote read access.


## Audio interfaces and delivery troubleshooting (0.8.6)

The same USB input may appear through MME, DirectSound, WASAPI or WDM-KS.
Keep the working interface selected; matching names are not interchangeable.
Open Audio, detection & recording, then Audio diagnostics to inspect/copy device
information and the last capture error without stopping reception. Default rate
is device-reported, not a complete list of supported rates. The report uses the
dialog input selection but saved channel/rate values. Device numbers may change
after reconnecting hardware; restart to refresh a stale PortAudio inventory.

Deliveries lists queued local time and the completed filename when available.
Select a row and click Details, or double-click it. Scroll horizontally to inspect
long filenames/results. A script receipt or text webhook is not FTP confirmation.

In Destinations & actions, Review tone sharing lists permission mismatches.
FTP/email/transcription require Allow external audio / transcript sharing on the
relevant tone sets. Transcript-bearing webhooks also require sharing permission.
Review each tone deliberately; permissions are never enabled automatically.
Changing permission affects future eligible pages, not previously skipped ones.


## Saving settings while monitoring (0.8.7)

Most settings can now be saved without manually stopping reception. Destination
changes affect future jobs; existing jobs keep their saved settings. Detector, tone,
discovery and recording changes wait until there is no active sequence/recording
and the input is quiet. Check the status line for pending/applied feedback.
Continuous traffic can postpone changes. Saving again replaces the pending set.

A change of input device, channel or sample rate automatically reopens the audio
stream at that boundary. This causes a brief reception gap, although monitoring
stays enabled. If the new input fails, inspect Audio diagnostics and select the
previous working input; the application retries, it does not silently substitute
a different device. Active recordings retain their encoding/name settings.
Pending changes are saved to disk and used on restart. During replay, detector
changes wait until replay ends. Coordination/identity changes and full settings
imports still require stopping. The coordinator service is configured separately.


## Reviewing unknown stacked pages

Enable discovery and local candidate recording before a test. Discovery settings has reviewable weekly-test starting values, an independent purity threshold, a frequency range and short dropout bridging. These starting values need validation against your radio; the 250 Hz lower limit excludes lower-frequency components but must be lowered if your paging tones are below it. The counters show short/overlong runs and low-purity frames since the last reset.

Select a candidate, then Review sequence / split stacked pages. Choose an observation and play the full recording. Ctrl-click two neighboring runs for an A/B draft, or select one for a long-tone draft. Repeat for each agency. A–B–C–D can be A/B plus C/D; the intermediate B/C candidate is not proof of a separate page. Drafts remain disabled and external sharing is off until you review and enable them. No source audio is overwritten or cut by this action. Old observations without saved gaps require recapture/reanalysis for splitting. Uncheck the hide-library-frequencies filter if you want to inspect timings for existing agencies.


## Recording filename time zone and log times

In Settings > Audio, detection & recording, choose Filename time zone: Local time
or UTC. Local time follows this computer's time zone and daylight saving for the
recording start. New installations use Local time; existing configurations retain
UTC until changed. Save to apply at the next safe recording boundary.

The filename's {date} and {time} describe recording start. {offset} adds a numeric
local offset (for example -0400) or UTC. Overview, Recordings and Discover Tones
show local time. A recording-complete row happens after recording start, so its
seconds normally differ from the filename. JSON numeric timestamps remain Unix
epoch seconds; they are not formatted local clock readings. Discord/message
{time} remains local event time. {filename} and {filename_url} use the actual name.
Existing files are not renamed; active and queued recordings keep their saved
settings. For example, 13:20:40 Eastern daylight time equals 17:20:40 UTC.


## Clear deleted recording entries

On Recordings, click Clear deleted to remove entries already marked deleted by cleanup from the visible list. Completed audio, active recordings and pending work remain. This clears list history only; internal recording metadata remains available for related events and deliveries. Clearing persists after restart. On startup and when Clear deleted is clicked, Tone Sentry checks completed recordings in its current audio folder and legacy recording folders. Files deleted outside the app are marked deleted too. Active/encoding recordings are skipped; permission or device errors are not treated as proof of deletion. Removing only the JSON sidecar does not mark an existing MP3 deleted.


## Live dispatch audio after tone detection

Open Settings > Audio playback device. Choose the output and check Play live
dispatch audio after tone detection, then Save playback device. This is off by
default. The tone set must have recording enabled. An accepted configured page
opens live listening; it follows the normal dispatch recording's silence, fixed
length and stop rules, continuing across maximum-length recording parts.

Discovery-only candidates, safe demos/WAV replay, ignored or record-only scheduled
tests, and suppressed duplicate pages do not start live listening. While listening,
later stacked tones or repeated pages can still be audible. This option does not
remove tones from the saved MP3 and does not play recording pre-roll.

Stop playback beside Play recording silences the current session without stopping
capture, recording or uploads. Live listening can resume with the next accepted
new dispatch recording. Playing a saved recording stops live listening; manual
playback takes priority over new live triggers until it finishes. Changing the
output or checkbox stops playback and applies to future triggers.

The output runs independently with a bounded buffer. A slow output drops playback
audio instead of delaying the detector. Output-device errors appear in the playback
status and do not stop recording or deliveries. Device startup and buffering add
latency and may lose the first audio if startup is slow. Use headphones or isolated
speaker routing so played audio cannot feed back into the radio input. This is
local speaker playback and does not require external-sharing permission.


## Start monitoring when the application opens

In Settings, check Start monitoring when Tone Sentry opens. This saves automatically
and takes effect on the next normal application launch using the saved input and
tone sets. It is off by default. Enabling it does not start capture immediately;
use Start monitoring for the current session. Stop monitoring still works normally.
If the saved input is unavailable, normal capture retries and error reporting apply.
Uncheck the option to keep future launches stopped. Settings imports preserve this
receiver-local preference. Demos and diagnostic launches never auto-start capture.
This does not add Tone Sentry to Windows Startup or start the app at computer boot.


## Compact Discover Tones controls

The meter occupies the left half of the top section; Reset gain, Auto gain and Save meter are on the right. Review stacked is beside Play recording and Stop playback. Create draft, Details, Export and Clear candidates use the same toolbar, which wraps on narrow windows. The status line includes Capture audio on/off. Detailed setup remains in Discovery settings and this guide; detector counters are no longer displayed above the candidate list.


## Compact Overview layout

Overview uses single-line status boxes with labels beside values. The boxes wrap into two rows if needed. The left half holds the shared signal/gain meter; Reset gain, Auto gain and Save meter are on the right. Playback actions remain directly above the activity table. These layout changes do not alter monitoring or recording settings.


## Remote web console (0.8.15 beta)

Use **Settings → Remote web console** to enable password-protected browser access.
It is off by default. For another computer or phone, choose listen address
0.0.0.0, enter the receiver's LAN/VPN IP as the browser address, keep port 8767,
create an administrator account with a password of at least 12 characters, and
save with Enable checked. Reopen the dialog to view the HTTPS URL and certificate
SHA-256 fingerprint. Compare that fingerprint with the browser certificate before
accepting its first-visit warning. Windows Firewall may require a private-network
inbound rule; the application does not create one or configure your router.

Open the URL from a device on the same private network or VPN and sign in.
Status shows local receiver time, signal level and pending edits. Tone library
provides forms to add/edit/delete or enable/disable tones. Recordings supports
search, playback/seek, download and Clear deleted. Playback uses the browser's
speakers. Activity shows events and remote command results.

Pause detections keeps input capture running and lets existing recordings finish;
Resume resets partial tones. Stop ends capture and can interrupt recording.
Queued deliveries continue. The desktop Overview also has Pause/Resume detections.
Changes wait for the same safe boundaries as desktop edits. Close desktop dialogs
before remote changes. If another editor changed settings, reload and review.

Accounts have Viewer or Operator/Admin access. Account and network administration
is local in this release. Saving web-access settings signs everyone out. Web
passwords are salted hashes kept outside receiver configuration exports. Sign out
on shared devices. Closing the desktop closes web access; closing a browser does
not stop the radio. Use a private LAN/VPN, not a public forwarded management port.

See the packaged docs/WEB-CONSOLE.md for the full setup and troubleshooting guide.
Browser live audio, web discovery/scheduler/destination editing and web access in
headless run mode are not part of this first beta.


## Web access updates in 0.8.16

Settings → Remote web console now shows local IPv4 addresses with adapter names
and connection status. Refresh local IPs updates that list. Look up public IP
contacts api.ipify.org only when clicked; it does not change your network or
listener settings. A VPN may change the result. These addresses are for reference;
a public address does not mean that remote internet access is configured.

Overview records each successful web sign-in with username, connecting IP address
and local date/time. Normal browser polling does not create repeated notices.
Rejected certificate handshakes no longer stop the Windows GUI web listener.
If another listener failure occurs, its exception type appears in Settings and
Overview. Save and apply web access restarts it. Close desktop dialogs before
performing browser control or tone edits.

Reset gain, Auto gain and Save meter now share one horizontal row on both Overview
and Discover Tones.


# Google Chat setup

Tone Sentry 0.8.17 adds one-way Google Chat incoming-webhook notifications. It is a standalone integration; no OpsHub or other website is required. Notifications contain text and optional links, not MP3 attachments or interactive commands.

## 1. Create the Google Chat webhook

Use a Google Workspace account with Google Chat and incoming webhooks permitted by your administrator. Google's current quickstart specifies Business or Enterprise Workspace. In a desktop browser, open your Chat space, select its title, then Apps & integrations > Add webhooks. Name it Tone Sentry, save, and copy its complete URL. If Add webhooks is unavailable, check with your Workspace administrator.

The URL contains a secret key/token. Keep it private. Tone Sentry saves it in local destination settings; protect the receiver data folder. No separate Google password, bearer-token environment variable, OAuth setup, or service account is needed for this webhook mode.

Official instructions: https://developers.google.com/workspace/chat/quickstart/webhooks

## 2. Configure Tone Sentry

Open Settings > Destinations & actions > Add destination.

- Destination name: a readable name such as Dispatch Google Chat.
- Destination type: webhook.
- Webhook message format: google_chat. Auto also recognizes complete official Google Chat webhook URLs.
- Webhook / transcription URL: paste the complete URL including key and token.
- Delivery scope: local for a standalone receiver. Shared is for configured receiver coordination.
- Google Chat message template: customize the text. Use Preview Google Chat message to inspect it without sending.
- Trigger: choose Recording complete for a recording link, or Tone detected for an immediate text alert. Selecting both sends separate messages.
- Agency filter: select agencies, or leave all unchecked for every agency.
- Enable destination, then Save destination.

Start with this template:

```text
{agency} - {time}
Receiver: {site}
```

## 3. Link an uploaded recording

Use Recording complete as the only trigger and select your FTP/FTPS destination under Wait for successful FTP upload. Both destinations must have the same delivery scope; enable the FTP destination for the same agencies. Allow external audio sharing on those tone sets so FTP can upload.

```text
{agency} - {time}
Listen: https://your-server.example/audio/{filename_url}
```

Replace the example with the HTTPS address that serves your FTP upload directory. An FTP host/directory is not automatically a browser download URL. The link must be accessible to recipients. Use {filename_url} for URL-safe filenames; {filename} displays the actual filename. Keep the FTP remote filename template blank when using this example, so the uploaded basename matches the recording basename.

## 4. Optional transcript messages

A separate configured transcription provider is required; this integration does not transcribe audio. Create a second Google Chat destination with Transcript complete, Include transcript checked, and a template containing {transcript}. Allow external audio / transcript sharing on the associated tone sets. Wait for FTP currently applies only to Recording complete webhooks.

## 5. Verify and troubleshoot

After a real eligible page, inspect Deliveries and confirm that the message appears in the intended space. Preview does not send; safe demo and safe replay do not send external notifications. This release was tested with local/mock delivery, not a real Google account.

HTTP 400: check message size and webhook URL. HTTP 401/403/404: check webhook validity and Workspace permissions; recreate the webhook if needed. HTTP 429 or temporary server/network failures use the background retry queue. Very large messages are rejected with a clear error rather than silently cutting off a recording link; shorten the template or omit the transcript. A timeout after Google accepted a message can cause a duplicate on retry; exactly-once delivery is not guaranteed.

If no job appears, check destination enabled, trigger, agency filter, delivery scope, repeat/test suppression and transcript-sharing permission. If waiting for FTP, inspect that upload's status first. Failures do not stop tone monitoring or recording.


## Notify-only alerts and discovery recording context

In Playback device (also under Settings > Audio playback device), choose Known-tone listening mode: Off, Notify only, or Live dispatch audio. Existing live-audio settings are preserved on upgrade; new beep options start off. Notify only plays a short 880 Hz beep through the selected output. Alert volume is 0-100; use Preview alert tone to try the current unsaved output/volume. Save playback device to apply. Beeps do not enable/disable recording or external delivery and can be used for tone sets with recording disabled.

Beep for discovered tone candidates is a separate opt-in checkbox. It alerts on measured candidates, including candidates corresponding to known frequencies; it does not identify an agency. Repeated observations of a candidate beep at most once per 60 seconds, and all alerts share a two-second cooldown. Closely stacked notifications may therefore share one audible indication. Known-tone alerts honor duplicate and scheduled-test suppression. Safe demo/replay produces no alerts. Discovery has no agency identity, so agency-specific weekly-test rules do not suppress its beeps; turn discovery alerts off during those tests if desired.

Manual playback and active live-dispatch audio take priority over alerts. Stop playback cancels the current beep/session, but a later eligible event can alert again. Output errors appear in playback status and do not stop capture. Avoid feeding speaker audio back into the monitored receiver input. Verify the physical output device and comfortable volume on the receiver computer.

Discovery recordings are labeled Discovery clip - overlaps [agency] when confirmed detections overlap the clip, or Discovery clip - unconfirmed otherwise. The overlap label is advisory: it does not claim every tone belongs to that agency. Review the full sequence for unidentified tones in stacked pages. No clip or candidate is discarded, merged, automatically enabled or externally delivered by this feature.

Recording/event JSON details and Discover Tones candidate details include known_page_overlaps with confirmed event IDs, times, agencies and associated normal recording IDs where available. The desktop and web recordings/activity views show the context. Older clips can gain context if their detection history is still in this receiver database; clearing visible history does not remove it. Existing filenames and old JSON sidecar files are not renamed or rewritten. New discovery sidecars include overlaps known at encoding time; the application view can show later matches. Missing detection history means an unconfirmed label, not proof of an unknown agency.
