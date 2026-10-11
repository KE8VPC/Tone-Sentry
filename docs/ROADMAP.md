# Next-release roadmap

Requested September 9, 2026; updated through the Tone Sentry 0.8.0 development build.

## Current progress

- October 7, 0.8.16: implemented the windowed Windows listener logging fix, clearer stopped-listener reporting, local adapter/IP references and on-demand public-IP lookup, successful web sign-in notices in Overview, and side-by-side meter controls on both tabs. Packaging/validation recorded in VALIDATION-0.8.16.txt; field overnight acceptance remains pending.

- October 7, 0.8.15: embedded HTTPS web console implemented for status, known-tone editing, recordings/playback/download, activity and start/pause/resume/stop. Accounts/network setup are local. Polling and owner-thread command queue; web editing is blocked while desktop dialogs are open. See WEB-CONSOLE.md. Web headless mode, discovery/scheduler/destination UI, browser account administration, public-network deployment and Pi rebuild remain future work.

- October 6, 0.8.14: Overview compact single-line summary boxes, half-width meter/right-side gain controls, and reduced spacing above the activity list. See VALIDATION-0.8.14.txt.

- October 6, 0.8.13: compact Discover Tones with half-width meter/right-side gain controls, no reset-counter row, inline review/playback actions that wrap on narrow windows, shorter guidance and tighter spacing. See VALIDATION-0.8.13.txt.

- October 6, design only: optional authenticated remote web console for status, tone editing, browser recording playback and receiver controls. Shared controller/one engine, safe-boundary edits, explicit detection pause versus receiver stop, roles and protected audio access. See WEB-CONSOLE-DESIGN.md. Historical design entry, superseded by the 0.8.15 implementation above.

- October 6, 0.8.12: check completed recording paths at startup and before Clear deleted to recognize external MP3 deletion. Preserve metadata/jobs and skip active/encoding files and access errors. Updated About beta narrative. See VALIDATION-0.8.12.txt.

- October 6, 0.8.11: optional Start monitoring when Tone Sentry opens checkbox, default off, saved for the next GUI launch. Diagnostics/replay do not auto-start capture; receiver-local import preservation and error behavior are tested. See VALIDATION-0.8.11.txt for source/package evidence.

- October 6, 0.8.10: optional live dispatch listening after accepted configured tone detection through the selected playback output. Bounded asynchronous output follows normal recording windows, skips suppressed/test/replay/discovery-only triggers, and yields to manual playback. Stop playback silences the current session. Physical output/capture coexistence remains a field check. This release also includes playback buttons beside recording controls, Clear deleted on Recordings, and the revised About creator description. See VALIDATION-0.8.10.txt for package checks.

- October 3, 0.8.9: recording filename time zone is selectable as Local time or UTC. New profiles use local time; older configurations/imports retain UTC. Active and queued encoding snapshots preserve the original choice. Local-time table headings clarify the difference between recording start and completion. JSON timestamps and existing files remain unchanged. See RELEASE-0.8.9.md and VALIDATION-0.8.9.txt.

- October 1, 0.8.8: Discover Tones now has a capture/review/split workflow with a measured sequence table, recent-observation selector and manual adjacent-pair/single-long-tone drafts. New observations preserve gaps. Discovery purity is independent of configured detection purity, brief same-frequency dropout bridging is configurable, and rejection counters plus reviewable weekly-test starting values aid setup. Local weekly-test analysis recovered five complete unidentified page groups, including the previously rejected close 638/653 Hz pair. The operator confirmed 136.5 Hz as channel CTCSS; the weekly-test discovery range excludes it. See DISCOVERY-WORKFLOW.md and VALIDATION-0.8.8.txt for package status.

- September 29: 0.8.7 implements destination updates for future jobs while monitoring, deferred tone/detector/recording changes at a quiet boundary, and automatic input reopening for device/channel/rate changes. Captured audio drains before switching; reopening has an unavoidable reception gap. Failed-input recovery does not wait indefinitely for missing tone endings. Existing queued deliveries and recording encoder/name settings are preserved. Coordination/identity and full settings import still require stopping. Source validation: 178 passed, one platform skip, two existing warnings. See RELEASE-0.8.7.md and VALIDATION-0.8.7.txt for package validation.

- September 18: 0.8.6 adds audio-interface labels, read-only copyable input diagnostics, specific capture-error details, queued time/filename columns and a Details button for deliveries, explicit sharing-permission feedback, and the header creator credit. Source tests pass; see RELEASE-0.8.6.md and VALIDATION-0.8.6.txt for packaging results. Live settings updates remain future work.
- Field report: four agencies now detect, record, upload by FTP and produce working Discord audio links after enabling external sharing. Recording lengths/cutoffs are satisfactory in reported tests. Other missed agencies need frequency/timing verification through discovery; overlapping dispatches remain best effort, not a release blocker. Reception now uses direct receiver audio via USB PnP input. Pi 5 hardware testing remains pending.

- September 16 follow-up: investigate duplicate-looking audio input choices observed on the overnight receiver using a USB PnP audio device. The input selector currently displays every input-capable PortAudio entry by index/name without its host API. Inspect the test machine's device/host-API inventory before deduplicating. Add understandable interface labels, consider a simple view with an advanced show-all option, preserve access to distinct physical devices with identical names and the saved selection, and test reconnect/restart behavior. Do not change the running overnight receiver's device selection automatically.

- September 15: private 0.8.5 Raspberry Pi 5 ARM64 test package prepared with installer, menu launcher and isolated diagnostics. Host tests/package checks pass; actual Pi installation and audio acceptance remain pending. See VALIDATION-PI-0.8.5.md.

- 0.8.5: destination editor filtering and simplified script-file selection are packaged in folder and portable Windows x64 test builds. 167 source tests passed (one Unix-only skip), and both packaged diagnostics passed. Subsequent script receipt logs and the field report above supersede the earlier deferred FTP/Discord investigation; see RELEASE-0.8.5.md and VALIDATION-0.8.5.txt for original package evidence.

- 0.8.4: the three delivery improvements listed below are now packaged in folder and portable Windows x64 builds, following Mike's request. All 159 source tests and both isolated executable diagnostics passed. The following source-only notes describe their earlier development stage; see VALIDATION-0.8.4.txt for current package status. The earlier Defender report remains unresolved.

- Next release, source only: clearer delivery status labels and a double-click details view with a related-upload button. Related jobs remain inspectable after clearing their displayed history, without exposing destination credentials or changing the queue. No new EXE yet.

- Next release, source only: recording-complete webhooks can wait for a selected FTP/FTPS upload. Waiting survives restarts without consuming retry attempts; failed/cancelled/missing uploads block the notification with an explanation. Config validation requires matching scopes. No new EXE yet.

- Next release, source only: Deliveries has a Retry selected menu with original-settings retry and reviewed retry using currently saved destination settings. It preserves delivery identity/recording and the original email recipient, rejects incompatible destinations and active/completed jobs, and updates the queue atomically. No new EXE yet; Mike will test closer to completion.

- 0.8.3: Settings Import adds file selection, a review before applying, a full local settings backup and rollback. Receiver-local bindings/deletion policy stay unchanged; imported destinations are disabled for review. See RELEASE-0.8.3.md.

- 0.8.2: FTP/FTPS upload directly into the configured folder without UUID subfolders; new MP3 names replace whitespace with underscores; shared `{filename_url}` supports URL-safe download links while `{filename}` preserves the actual name. Local upload/retry/collision and template tests pass. Existing remote files are not moved.

- 0.8.1: normal masked FTP password entry with user-selected Base64 configuration storage, shared by FTP/FTPS tests and deliveries. Settings exports omit saved FTP passwords. Legacy environment-variable credentials remain supported. Base64 is not encryption; see RELEASE-0.8.1.md.

- 0.8.0: compact header/tab controls and shared meters; condensed receiver details; six-character local MP3 suffixes; shared `{filename}` templates; default Windows `ToneSentryData` migration; FTP login/directory validation; masked password-reference fields; and reorganized help are implemented. See RELEASE-0.8.0.md for test evidence and migration/field limitations.
- 0.7.0: shared Auto gain/meter saving, selectable playback output, and additional delivery clearing shipped in folder-style and single-file Windows test packages.

- 0.6.0 update: live input gain and tricolor meter, persistent history clearing, editable destination names, flat local `audio/` storage for new clips, and formatted/navigable help are implemented. See RELEASE-0.6.0.md for validation and transition limits. Existing files are not automatically moved; coordinator archive isolation is retained.

- Implemented: Tone Sentry display branding, About credit, persistent Light/Dark selection, local candidate audio with configurable silence stopping, playback of recent observations, and explicit main/dialog icon assignment.
- Verified locally: synthetic audio and desktop tests; Windows source preview shows the approved title-bar icon and readable dark-theme forms. Compiled build acceptance is recorded separately in RELEASE-STATUS.md.
- Native compilation with Nuitka replaces application bytecode packaging for the 0.5.0 development bundle. Public redistribution still needs corresponding-source preparation for bundled third-party components; see NATIVE-BUILD.md.
- Registration foundation is implemented and tested. Mike selected an **unrestricted development release**. Publisher key provisioning, commercial policy, recovery/transfer policy and any feature restrictions remain pending.
- Remaining: field RF and long-duration tests, native Linux/macOS/ARM builds, additional display-scaling/icon checks, code signing, and further creator information from Mike.

The sections below retain the requested scope and acceptance criteria; they are not all claims of completed validation.

## Settings import — implemented in 0.8.3

- Add an **Import settings** button alongside the existing settings export option. Accept Tone Sentry's exported settings files through a file picker.
- Validate the file and show a readable summary of changes before applying it. Explain invalid or incompatible settings without requiring JSON editing.
- Back up the current settings before applying an import; leave them unchanged if validation or applying the import fails.
- Preserve this receiver's identity by default when importing settings from another machine. Flag unavailable audio devices, machine-specific paths and missing credential references for review.
- Explain which settings the export includes and which need to be configured again. Importing must not run scripts or send test notifications automatically.
- Add step-by-step export/import instructions to Help & how to and verify an export/import round trip, malformed files, version compatibility and recovery after failure.
- Status: implemented in 0.8.3. Receiver-local bindings and deletion policy are preserved; imported destinations remain disabled and FTP passwords must be entered again. See RELEASE-0.8.3.md.

## About tab

- Add a main-window **About** tab.
- Display the exact credit **Created By:  Mike Beam**.
- Include application name and version, with space for further information Mike will provide later.
- Keep third-party acknowledgments accessible. Do not invent a biography, contact details, organization, or additional credits.

## Selectable dark theme

- Offer **Light** and **Dark** in Settings and remember the choice across restarts.
- Apply the theme consistently to all tabs, dialogs, tables, selection states, input fields, menus, help, JSON details and previews.
- Preserve readable contrast and visible focus indicators, including disabled controls and status messages.
- Verify switching themes without changing receiver settings or interrupting audio processing.

## Original product name

Selected product name: **Tone Sentry** (chosen by Mike).

Suggested subtitle: **Paging Monitor & Tone Discovery**.

Tone Sentry emphasizes continuous tone monitoring and detection. Retain the approved orange paging beacon and radio-wave icon. Name availability, existing-product conflicts and trademark status have not been checked; selection is not a claim of exclusivity.

The 0.5.0 branding release updates window titles, About/help text, executable metadata, release filenames and documentation to Tone Sentry. Existing data-folder discovery, instance IDs, tone IDs and integration contracts are preserved. Mike selected the two-word form on September 10; filenames use Tone-Sentry.

## Resistance to reverse engineering

Objective: make proprietary application logic harder to recover from distributed binaries. No locally executed program can be made impossible to reverse-engineer.

- Evaluate a native compilation build with Nuitka, or compile sensitive detection/discovery modules with Cython before packaging. Choose only after testing Tk, NumPy, PortAudio, FFmpeg, resources, TLS and the full receiver workflow.
- Keep the development source private. Future public/customer release bundles should contain compiled application artifacts and required resources/notices, not source ZIPs, tests, build intermediates or debugging symbols. Preserve existing development sources and archives; this roadmap does not delete anything.
- Inspect the final artifacts for application `.py`/`.pyc` files and unintended source inclusion. Document remaining exposure, including strings, resources and configuration formats. Native compilation increases effort; it is not an absolute secrecy guarantee.
- Continue keeping credentials out of compiled code. Retain third-party notices and satisfy dependency distribution requirements.
- Evaluate code signing separately for publisher identity and integrity. Signing is not a source-concealment technique. Purchasing certificates or commercial tooling is not part of this roadmap entry.
- Compare startup time, CPU/memory use and audio reliability with the current build. Repeat all tests and the frozen synthetic self-test; field reception must remain reliable.
- Preserve standalone offline operation; do not introduce server-dependent detection or licensing merely to hide code.

The older PyInstaller executables bundle Python bytecode and are not source-protection solutions. Already distributed source or binaries cannot be made private retroactively.

Technical references reviewed September 9, 2026:

- [PyInstaller: hiding source code](https://pyinstaller.org/en/stable/operating-mode.html#hiding-the-source-code)
- [Nuitka user manual](https://nuitka.net/user-documentation/user-manual.html)

## Playable recordings of discovered tone sets

Requested September 9, 2026. Extend Discover Tones discovery to retain actual intercepted audio for potential new tone sets, rather than measurements alone.

- Add an **Record discovered candidates** checkbox in Discovery settings.
- Capture a candidate's tone sequence and following radio audio. Keep a pre-roll buffer long enough to preserve the first tone even when the candidate is recognized after it ends.
- Use silence detection to stop recording automatically. Provide controls for silence threshold, required continuous silence, minimum recording duration, post-roll and maximum recording duration. The maximum duration prevents an open carrier or continuous noise from recording indefinitely.
- Do not stop during the normal gap between A/B tones or short pauses within stacked pages. Associate all candidates in a shared recording with that recording, while retaining the ambiguity labels for possible pair boundaries.
- Add a **Play recording** button to the Discover Tones tab and candidate-details popup. Play the captured audio, not a synthesized approximation. Clearly indicate recording, encoding, ready, missing and purged states.
- Save playable MP3 clips with candidate IDs and timing metadata. Retain links to recent individual observations so repeated detections of a frequency group can be reviewed separately.
- Include discovered clips in the Scheduler retention policy and existing recording storage protections. Preserve candidate measurements when associated audio expires, and show that the audio is no longer available.
- Keep discovered audio local by default. Recording an unknown candidate must not automatically enable a tone set, send alerts, run scripts or upload audio. Playback must not feed the detector or trigger another detection.
- Verify pre-roll preservation, silence-based stopping, maximum-duration stopping, stacked candidate association, repeat-observation playback, restart recovery and retention behavior. Confirm that discovery recording does not disrupt normal configured-tone recording.

## Registration key to unlock the full version

- Add a **Registration / License** section in Settings or About, with a registration-key input and **Activate full version** button.
- Show the current edition and activation status, with clear feedback for accepted or invalid keys. Remember successful activation across restarts and application updates.
- A valid registration key unlocks the full-version features without requiring a separate application installation or losing existing settings, tone sets, recordings or receiver identity.
- Unlicensed-version limits selected by Mike: **1 destination**, **3 tone sets**, **no settings export or settings import**, and **standalone/solo mode only — no receiver coordination**. These are planned restrictions, not limits enforced by the current unrestricted development build.
- Implement and test these limits consistently across the interface, configuration loading and runtime entry points so configuration editing cannot bypass them. Preserve existing data when a configuration exceeds the limits; provide a clear review/activation path rather than silently deleting destinations or tone sets. Define the treatment of existing over-limit development configurations before enabling enforcement.
- Pricing, trial duration, license expiry, device/receiver limits, transfer policy and any other full-version feature rules remain unspecified.
- Design key issuance and validation so only authorized keys unlock the full version; keep key-generation secrets outside the distributed application. Choose offline validation or an activation service after the licensing policy is defined, while preserving reliable offline operation after activation.
- Plan license recovery and transfer between computers. Do not expose complete registration keys in logs, diagnostics or routine exports.
- Handle registration failures without deleting user data or abruptly interrupting an active recording. Test activation, restart/update persistence, invalid keys, offline behavior and any agreed license limits.

Offline verification and a publisher-only issuer utility are implemented for 0.5.0. No publisher signing secret has been provisioned, no activation service is required, and no registration restriction has been added.

## Fix Windows title-bar icon

Reported September 9, 2026; deferred at Mike's request.

- The upper-left corner of the application title bar shows a generic window icon instead of the approved orange beacon/radio-wave icon.
- Reference: user-supplied `C:/Users/wapak/OneDrive/Desktop/Screenshot 2026-09-09 223010.png`. The screenshot demonstrates the title-bar issue; it does not establish whether the executable, shortcut or taskbar icons are affected.
- Investigate how Tk applies the small title-bar icon in the packaged Windows executable, including the interaction between `iconphoto`, `iconbitmap`, default dialog icons and Windows application identity. Root cause is not yet confirmed.
- Verify the corrected icon visually in the actual packaged application at common Windows display scaling settings, including the main window and dialogs. Check taskbar and File Explorer icons separately for regressions; embedded-resource checks alone are not sufficient.

Explicit main-window and dialog icon assignment has been applied. The source preview shows the beacon in both title bars. Compiled-binary verification and remaining scaling checks are tracked in release status.

## Cleaner audio and recording JSON layout

Requested September 10, 2026. Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Store recordings and their accompanying JSON metadata directly in an `audio/` folder under the receiver's data directory, for example `audio/2026-09-10_14-30-00_Wapak-FD.mp3` and its matching `.json` file.
- Do not put the instance ID in the audio folder name or create an instance-ID subfolder. Keep receiver identity in metadata/database records for redundant receiver coordination.
- Apply the layout to configured-page recordings and discovered-tone clips. Retain filename controls and collision protection so repeated or simultaneous captures cannot overwrite each other.
- Provide a safe transition from the existing `recordings/<instance-id>/` layout. Preserve existing playback links, candidate observation links, queued deliveries, interrupted encoding recovery and Scheduler retention; do not move files still in use.
- Keep application configuration and operational databases separate from recording sidecar JSON. This request concerns the recording file layout, not removal of receiver identity from coordination.
- Verify new capture, MP3/JSON pairing, playback, cleanup and existing-recording compatibility before shipping the change.

Implementation note: new local MP3/JSON files use `audio/`. Existing recordings remain in place and continue working; no automatic file migration is performed. Coordinator archives retain receiver-isolated storage.

## Simplify Script destination setup — implemented in source

- Replace the executable-and-arguments row editor in normal Script destination setup with one **Script file** path entry and a **Browse** button.
- Let the operator select a Windows .bat/.cmd file or a suitable Linux/macOS script file without manually entering an interpreter, command switches or quoting.
- Use the operating system's configured file association/launch behavior where it supports execution. Verify actual behavior on each platform: some associations open an editor, while Unix scripts may require an executable permission and interpreter declaration. Provide a plain-language explanation when a selected file cannot be executed; do not silently report opening an editor as successful script execution.
- Handle paths containing spaces. Preserve existing configured script destinations and document a migration path, including the filename argument used by the existing receipt-log example.
- Keep applicable shared destination controls (enabled state, triggers, tone filters and delivery scope). Selecting or saving a file must not execute it.
- Verify supported file types, missing files, launch failures, completion/timeout reporting and restart/retry behavior on the supported platforms. Update Help with the simplified workflow.
- Status: implemented in source after 0.8.4, not yet packaged. Windows .bat/.cmd files use the system batch interpreter; executable Linux/macOS scripts use their #! declaration, rather than arbitrary editor/file associations. The MP3 basename is automatically passed as argument one. Existing argv destinations remain intact unless a replacement file is selected. Windows execution is tested; Unix execution remains pending. The remote test configuration was not changed.

## Destination settings: show only relevant controls — implemented in source

- Show only the fields, explanatory text, previews and actions that affect the selected destination type; retain applicable shared controls such as name, enabled state and delivery scope.
- FTP/FTPS selection shows FTP credentials, directory, filename options and connection testing, with FTP-specific help only for these types.
- Show the Discord template, Discord help and Discord preview only for a Discord webhook, including Auto mode when the entered URL is recognized as Discord. Generic webhooks show their own applicable options instead.
- Apply the same filtering to email, transcription and script settings, including recipient lists, provider fields, headers, script arguments, trigger choices and template previews as appropriate.
- Update visibility immediately when destination type, webhook format or Auto-detected webhook type changes. Collapse hidden sections without leaving unused space.
- Switching types during editing should preserve entered values for switching back; hidden options must not interfere with validation of the selected type.
- Verify each type and webhook format, switching without saving, saved/reopened destinations, and compact layouts. Update Help to match.
- Status: implemented in source after 0.8.4, not yet packaged. Fields, notes, previews, recipient/provider/header editors and triggers follow the selected type and Discord Auto URL detection. Type switching retains unsaved form values; saving includes only applicable settings. Fixed recording-only destinations show an explanatory note instead of irrelevant trigger checkboxes.

## Editable destination names visible in lists

Requested September 10, 2026. Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Make the user-facing destination ID/name editable in the settings interface so an operator can identify a destination without opening its configuration.
- Display the chosen name prominently in the destination list and relevant delivery/job views, alongside destination type and enabled status. Examples: `Wapak Discord`, `Dispatch Email`, and `Audio FTP`.
- Keep a stable internal identifier for queued jobs and references, separate from the editable display name. Renaming a destination must not create a second destination, lose delivery history or invalidate pending jobs.
- Give existing destinations a readable fallback until renamed. Validate nonempty names and handle duplicate names clearly without exposing credentials or webhook tokens in labels.
- Verify creation, rename/save/restart persistence, list visibility and pending-job/history continuity.

## More readable and detailed Help & How To

Requested September 10, 2026. Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Rewrite the Help & How To guide in clear, user-friendly language with more detailed step-by-step instructions. Explain settings in terms of what the operator should choose and what happens next.
- Use **bold, underlined titles** for every section in the displayed help window. Render actual text formatting rather than showing Markdown symbols to the reader.
- Increase font size slightly for all help text, including paragraphs, lists, examples and notes; make section titles larger and easy to distinguish. This font-size request applies to the help guide.
- Improve spacing, paragraph length and examples so the guide is easy to scan and follow. Include an accessible section list or table of contents for longer guidance.
- Cover first setup, radio/audio input and levels, tone configuration and imports, monitoring, Discover Tones and clip playback, recordings and JSON details, weekly test schedules and retention, destination setup and notifications, redundant receivers, appearance and About, and common troubleshooting.
- Explain common failures and recovery steps, including missing audio, recordings that do not stop, duplicate pages, unavailable playback, delivery errors and permission/credential setup. Clearly distinguish local testing from live notifications.
- Keep the guide accurate for the installed version; label unavailable or planned features explicitly. Verify readable contrast in Light and Dark themes, text wrapping, scrolling and readability at common Windows display scaling settings.

## Reorganize Help & How To into a practical reading order

Implemented for 0.8.0: reordered help with consolidated quick start/troubleshooting and updated section navigation.

- Organize the in-app guide and related Windows/portable instructions around the operator's workflow, rather than the order features were added. Use this proposed sequence: introduction and quick start; installation, data folders and first launch; radio input, meters and gain; tone setup, reference chart and imports; monitoring, stacked pages and duplicates; Discover Tones; recordings, playback output and JSON details; weekly test schedules and retention; notifications and destinations; delivery/history management; multiple local and remote receivers; appearance and About; troubleshooting; advanced reference.
- Keep related instructions together, consolidate repeated setup and troubleshooting passages, and link to detailed sections from the quick start instead of duplicating them. Place prerequisites before the steps that depend on them.
- Match the section navigation/table of contents to the new order, use consistent plain-language headings across guides, and retain the larger text and bold, underlined in-app section titles.
- Preserve all existing guidance, including separate receiver identities and data folders, safe demo versus live notification behavior, playback feedback prevention, and recovery steps. Clearly distinguish available features from roadmap items.
- Verify that a new user can follow first launch through a successful local test in sequence, that experienced users can find individual settings quickly, and that packaged help matches the source guide for the release.

## Commercial release preparation

Requested September 10, 2026, following the licensing discussion. Todo only; no customer distribution, license change or dependency replacement is authorized by this entry alone.

- **Proprietary application license:** Prepare a commercial license agreement for Tone Sentry's own code and paid registration model. Clearly identify third-party components and preserve the rights granted by their licenses; do not apply blanket copying, modification or reverse-engineering restrictions to every bundled component. Confirm ownership and rights to included material before making proprietary licensing claims.
- **Simpler encoder packaging:** Evaluate a minimal FFmpeg build containing only the audio features Tone Sentry needs, without the current GPL video libraries. Prefer an appropriate LGPL configuration if feasible, while recognizing that LGPL components still carry notice, source and other distribution obligations. Preserve ordinary file/command-line communication with the separate encoder and verify MP3 encoding and recovery after any replacement.
- **Complete third-party compliance:** Inventory the exact shipped dependency versions, linked libraries and compiler/runtime components. Include required license texts and notices, and prepare a compliant corresponding-source/build-material delivery method wherever required. Verify the materials match the shipped binaries; upstream links alone have not been established as sufficient for the current FFmpeg package. These checks apply to paid/private customer distribution as well as public downloads.
- **Dependency and asset rights review:** Review application dependencies, compiled runtime components, the supplied tone-reference PDF, artwork and any other incorporated third-party material. Confirm redistribution permissions and attribution requirements; replace material whose rights cannot be established. Record findings against the final package rather than assuming that a package-level license covers every bundled file.
- **Final commercial/legal review:** Have a software-licensing attorney review the actual installer/ZIP, dependency/source delivery, proprietary customer agreement and registration terms before selling or distributing the commercial release. Assess whether the application and encoder remain separate works in the final design. Do not treat subprocess use or native compilation as an automatic legal exemption.

The commercial objective is a paid application whose own source can remain private while complying with third-party terms. Open-source dependencies do not inherently prohibit charging money. The current development build remains unrestricted; license policy, publisher-key provisioning and commercial distribution approval remain pending.

Reference discussions: [GNU FAQ on selling software](https://www.gnu.org/licenses/gpl-faq.en.html#DoesTheGPLAllowMoney), [separate versus combined programs](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation), [GPLv3 distribution terms](https://opensource.org/license/gpl-3.0), and [FFmpeg licensing guidance](https://ffmpeg.org/legal.html).

## Clear completed deliveries

Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Add a **Clear completed** button to the Deliveries log so the operator can remove completed entries from the visible history.
- Clear only successfully completed deliveries. Preserve pending, active, retrying, failed and ambiguous deliveries for processing or review.
- Keep the cleared history hidden after refresh and restart. Preserve internal job identifiers and duplicate-delivery protections so clearing the display cannot resend a delivery.
- Do not delete recordings, recording JSON files, destination settings or unrelated event history when clearing completed deliveries.
- Show how many entries were cleared, with a clear empty state when none remain. Verify mixed-status logs and continued background processing.

## Clear Overview activity and other appropriate history

Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Add a **Clear all** button to the Overview activity log to clear all currently displayed activity history. New events must continue appearing normally while monitoring runs.
- Keep cleared entries hidden after refresh and restart. Preserve internal detection, duplicate-suppression, recording and delivery references so clearing the display cannot cause repeat alerts or break playback and queued work.
- Review other history views for useful clearing controls, particularly Discover Tones candidate history and receiver/coordinator diagnostic history where available. Use consistent placement and explicit labels such as **Clear history**, **Clear candidates** or **Clear completed**, according to what is actually affected.
- Keep the separate **Clear completed** action for Deliveries. Clearing a history view must not silently cancel pending deliveries, stop active recording, remove configured tones or destinations, revoke receivers, or delete MP3/JSON files.
- In Recordings, distinguish clearing displayed history from deleting audio files. Any file-deletion action must state that files will be deleted and show the affected scope before execution; retain Scheduler retention as a separate operation.
- For **Clear all** and other broad history-clearing actions, explain the scope and offer confirmation or an undo path. Report how many entries were cleared and provide an informative empty state.
- Verify clearing during monitoring, concurrent arrival of new events, refresh/restart persistence, empty logs and preservation of ongoing recording/delivery behavior.

Implementation note: Overview and Discover Tones have clearing controls. Deliveries now also clears cancelled entries and all current entries; changed delivery outcomes reappear. Recordings and the current receiver-status view intentionally have no history-clear action: audio deletion remains on Scheduler, and live receiver state is not a log.

## Input-level adjuster and tricolor meter

Implemented for the 0.6.0 development build; field/UI acceptance limits are recorded in RELEASE-0.6.0.md.

- Add an input-level slider overlaid on the input signal strength meter in Overview, allowing adjustment while watching the live level. Keep the slider handle and level indication visually distinct and easy to operate.
- Use a conventional three-color volume meter: **green** for normal levels, **yellow** as the signal approaches the upper range, and **red** for excessive input level or clipping. Show green/yellow/red zones along the meter rather than relying only on a single changing fill color.
- Provide an accessible numeric gain value, keyboard adjustment and a reset-to-default control. Remember the selected gain across restarts and apply changes smoothly without restarting monitoring or interrupting recordings.
- Measure and display the level after the application's gain adjustment, with a peak/clipping indicator so brief overloads are visible. Choose and document consistent thresholds through testing; distinguish usable signal level from actual clipping.
- Make clear that this control adjusts application input gain. If audio is already clipped at the radio or sound-device input, advise lowering the upstream hardware/input volume; reducing software gain cannot restore the lost waveform.
- Keep labels and overload indication readable in Light and Dark themes and provide a text or icon indication alongside color. Verify meter/slider layout at supported window sizes and common display scaling settings.
- Verify quiet, normal, near-limit and clipped input, saved gain restoration, live adjustment during capture, and consistent gain application to detection and recording without accidental double amplification.

## Larger gain handle and optional automatic gain

Implemented for the 0.7.0 development build; automated checks and remaining hardware acceptance are documented in RELEASE-0.7.0.md.

- Make the orange input-gain handle larger and easier to see and grab. Increase its clickable/drag area as well as its visible size, while keeping the signal meter and peak marker readable at different display scaling settings.
- Add a clearly labeled **Auto gain** checkbox or Manual/Auto selector beside the meter. Keep manual gain as the default and remember the selected mode across restarts.
- In Auto mode, adjust application gain gradually toward a suitable signal range, with bounded minimum/maximum gain and controlled attack/release behavior. Show the current applied gain and make the active mode obvious.
- Prevent gain from rising excessively during silence, background noise or an open squelch. Reduce gain promptly for excessive post-gain levels without rapid oscillation or audible pumping. Automatic software gain cannot repair clipping already present at the radio or sound-device input; retain the upstream clipping warning.
- Define manual-handle behavior in Auto mode clearly: dragging the handle should return to Manual mode at the selected gain, with the mode indicator updating immediately. Allow switching modes without restarting monitoring or interrupting recording.
- Verify weak/strong signal transitions, silence/noise, clipped input, startup and saved settings, manual override and operation alongside configured-tone detection and discovery. Confirm automatic gain does not materially degrade tone timing, detection reliability or recording quality before enabling it for field use.

## Additional Deliveries clearing controls

Implemented for the 0.7.0 development build; automated checks and remaining hardware acceptance are documented in RELEASE-0.7.0.md.

- Add **Clear cancelled** and **Clear all** buttons to Deliveries alongside the existing **Clear completed** control.
- **Clear cancelled** hides only cancelled entries from the displayed history, preserving their internal records and cancellation state.
- **Clear all** clears the displayed delivery history across statuses. Explain before confirmation that this clears the view only: pending/running jobs continue, and clearing does not cancel work, retry jobs or reset duplicate-delivery protection.
- Hidden unfinished jobs must reappear when their status or attempt count changes, so subsequent retries, failures or completion remain visible. Newly created jobs must appear normally. Clearing must not silently conceal later outcomes.
- Preserve recordings, JSON files, destination settings, job identities, retry state and retention protections. Keep **Cancel selected** as a separate action that actually stops further attempts where allowed.
- Persist clearing across refresh/restart, report the number of entries cleared, and verify mixed-status logs, concurrent processing, new status changes and repeated clearing.

## VU meter controls and saving on Discover Tones

Implemented for the 0.7.0 development build; automated checks and remaining hardware acceptance are documented in RELEASE-0.7.0.md.

- Show the input VU/level meter and gain controls on **Discover Tones**, so the operator can monitor and adjust input levels without returning to Overview.
- Include the tricolor level display, clipping indication, larger orange gain handle and planned Manual/Auto gain selection consistently with Overview as those features become available.
- Provide a clearly labeled **Save meter settings** control and saved-state feedback for the shared input-gain/meter configuration. Preserve the selected configuration across restarts.
- Keep both tabs synchronized: they display the same receiver input and applied gain, not separate gain stages. Changing or saving settings on either tab must update the other and must not amplify audio twice.
- Allow adjustment and saving during discovery without restarting reception or interrupting recording. Verify synchronization, saved-setting restoration and layout/readability in both themes.

## Selectable audio playback device

Implemented for the 0.7.0 development build; automated checks and remaining hardware acceptance are documented in RELEASE-0.7.0.md.

- Add an **Audio playback device** dropdown in Settings, separate from the radio input-device selection. List available output devices with readable names and a **System default** option.
- Apply the selected output consistently to playback from Overview, Recordings and Discover Tones, including individual candidate observations.
- Remember the choice per receiver data folder across restarts. Provide a device-list refresh action and a clear message if the saved output is disconnected or unavailable; allow the operator to select another output.
- Implement application-controlled playback or an equivalent mechanism that can actually select the output device. The current default-player launch cannot guarantee that the selected device is used. Provide stop playback and clear playing/error feedback.
- Keep playback independent of the monitored input and recording pipeline. Explain that speakers or loopback routing can feed replayed audio into the receiver; choosing an output device alone does not prevent acoustic or system-level feedback.
- Verify system-default output, explicit speakers/headphones selection, device removal/reconnection, saved-device restoration, playback from all supported views and simultaneous monitoring without changing the receiver input.

## Rename the default Windows data folder to ToneSentryData

Implemented for 0.8.0; migration behavior and remaining acceptance are documented in RELEASE-0.8.0.md.

- Replace the legacy default `%USERPROFILE%\TonePageDetectData` with `%USERPROFILE%\ToneSentryData`, using the requested folder name `ToneSentryData`. Keep the default under the Windows user profile rather than assuming a writable drive-root folder.
- Provide a safe migration path for existing installations. Preserve receiver identity, settings, tone sets, schedules, destinations, recording files and JSON, discovery history, queued deliveries, and duplicate protection. Update stored recording paths where necessary; do not silently start an empty receiver or duplicate pending deliveries.
- Handle an existing old folder, an existing new folder, both folders, and interrupted migration without overwriting data. Do not move a folder while a receiver is using it. Retain a recoverable original until migration has been verified.
- Honor explicit `--home` folders and keep multiple receivers isolated. Update in-app help, Windows and portable testing guides, examples, and packaging instructions to use the new default.
- Verify fresh startup, migration and restart, playback of existing recordings, delivery continuity, and explicit custom data folders before release.

## Short recording ID suffixes in MP3 filenames

Implemented for 0.8.0 for new local recordings; existing names and full internal identities are preserved.

- Replace the full UUID appended to MP3 filenames with an ID suffix of at most six characters, retaining the configured timestamp and filename controls. Apply this to configured-page recordings and Discover Tones clips.
- Retain full internal recording UUIDs in the database, JSON metadata, delivery references and coordination messages. The shorter suffix is a filename convenience, not a replacement for internal identity or duplicate-page suppression.
- Use the same filename stem for each MP3 and its matching JSON file. Preserve playback, queued delivery and retention references when resolving the final path.
- Use collision-safe file reservation and regenerate a suffix on conflict without exceeding six characters. Never overwrite an existing recording or sidecar; timestamps reduce collisions but do not guarantee uniqueness for simultaneous captures, repeated timestamps or custom templates without a timestamp.
- Leave existing recordings and their references intact. Update filename examples and help for new recordings, and verify simultaneous captures, forced suffix collisions, restarts, discovery clips, playback and delivery references.

## Shared recording filename placeholder for templates and actions

Implemented for 0.8.0: Discord, generic webhook messages, email subject/body templates, FTP remote basename templates and script arguments. Before completion the filename is empty. Coordinator notifications use the actual coordinator archive basename.

- Add `{filename}` as a shared placeholder across relevant templates and actions, including Discord messages, other webhook templates, email subjects and bodies, script arguments, and transfer destination templates where supported. Reflect support in the corresponding settings interfaces rather than limiting it to Discord.
- Resolve it consistently to the actual completed MP3 basename, including `.mp3`, without exposing the local folder path. Use a common placeholder definition and resolution behavior across integrations. It must not refer to itself within the template that initially creates the recording filename.
- Read the finalized recording filename rather than reconstructing it from the message timestamp or template. Honor custom naming, collision resolution, and the planned six-character filename ID suffix.
- Document that the filename becomes available once the recording is complete and can be used by later related actions. Define and explain consistent behavior for earlier events or events without a completed recording; do not invent a filename. Preserve `{recording_id}` as a separate placeholder.
- Update validation, placeholder lists, unsent previews and Help & How To for every supported template field. Include examples for notifications and actions, and distinguish existing template support from fields that need new template controls.
- Verify consistent resolution across supported integrations, completed recordings, events without audio, custom names, retried deliveries, and coordinated recordings where applicable. Preserve each destination's escaping, argument handling and path validation. Adding filename text does not itself attach or upload the MP3.

## Compact interface for lower-resolution screens

Implemented for 0.8.0, with source geometry/scaling checks and visual review. Additional hardware/display acceptance remains pending. Visual reference: the user-supplied `Screenshot 2026-09-10 192818.png` showing the header and two separate action rows.

- Move the tagline "PAGING MONITOR & TONE DISCOVERY" to the left, directly beneath "TONE SENTRY". Place the upper-right action buttons in the dark header area currently occupied by the tagline.
- Combine Help & how to, Run safe demo, Replay WAV, Start/Stop monitoring, Stop playback, and Playback device into one horizontal button row. Keep labels on one line and preserve the Start/Stop monitoring state and its visual prominence. Reduce button padding and spacing as needed while retaining readable labels and usable click targets.
- Compact receiver-name and playback-status information beneath the header, reclaiming the space left by the moved button rows. Reduce excess header height, margins and padding so useful tab content is visible sooner.
- Evaluate a slim horizontal combined gain slider/input meter inspired by the user-supplied `Screenshot 2026-09-10 193917.png`: rounded track, filled level indication and a clearly visible vertical gain handle. This is an optional design direction if it improves lower-resolution usability, not a requirement to copy the image's time labels or playback behavior.
- Keep measured input level and adjustable gain visually distinct in the compact control. Preserve green/yellow/red level zones, peak/clipping feedback, a readable gain value, and a generous draggable hit area even with a slimmer appearance. Keep Auto gain, Reset and Save accessible nearby, and apply the same shared control to Overview and Discover Tones. Verify that compaction actually frees useful space without making adjustment harder.
- Review every tab and settings dialog for unused space, oversized cards, excessive section gaps, and unnecessarily tall controls. Group related controls into concise rows where practical and prioritize usable space for histories, recordings, tone lists and meters. Compaction must not undo the requested larger gain handle or readable help text.
- Make resizing practical on lower-resolution displays; do not rely solely on adding scrolling to an otherwise oversized layout. Keep controls reachable without overlap, clipping or forced multiline action rows. Retain scrolling where content genuinely needs it.
- Verify header/button fit and tab navigation at representative smaller window sizes and displays, including 1024x768 and 1366x768 where feasible, plus Windows scaling at 100%, 125% and 150%. Test both themes, long site names, active monitoring/playback status, and all tabs/dialogs; document any minimum usable size honestly.

## FTP destination connection validation

Included in 0.8.0; not present in earlier 0.7.0 executables.

- FTP and FTPS destination editors have a Test FTP connection button using current unsaved form values. Testing runs in the background and reports connection, credentials/login, TLS or directory-access failures without exposing raw server replies.
- Successful login plus entering the configured directory and querying its location verifies directory access without creating files or directories. This does not verify upload permission or a working data-transfer channel. Saving/enabling the destination remains a separate action.
- Automated checks cover a local FTP server with read-only directory permissions, missing directories, rejected credentials, missing secrets, GUI use of unsaved settings, and simulated certificate-verified FTPS setup. Live remote-server and real FTPS acceptance remain unverified.

## Mask password-reference fields in destination settings

Included in 0.8.0; existing 0.7.0 executables are unchanged.

- FTP and SMTP password environment-variable fields display asterisks when opened and edited, preserving the underlying value used for saving and connection tests.
- These fields still expect environment-variable names, not literal passwords. Display masking prevents casual on-screen reading; it does not encrypt configuration files or change credential storage.

## Condensed receiver summary

Included in 0.8.0. Site, Instance ID, Mode and Coordinator Status use one line per label/value. Group/Coverage, Outage Policy and Enrolled Receivers retain their separate sections.

## Notify-only audible alerts for detection and discovery

Requested October 8, 2026. Planned for future development; not implemented in the current build.

- Add an optional short alert tone / beep instead of live dispatch audio playback (Notify only mode).
- Allow separate enable/disable choices for accepted configured-tone detections and newly discovered tone candidates. Alert on candidate events, not continuously on individual audio-analysis frames.
- Play alerts through the selected playback audio device, with an alert volume control and a preview/test button. Present Off, Notify only and Live dispatch audio clearly; discovery alerts remain a separate opt-in setting.
- Keep detection, recording, FTP uploads, transcription and other deliveries independent of the audible notification mode. Notify only changes local listening behavior, not recording or delivery eligibility.
- Honor applicable duplicate and scheduled-test suppression for known tones, and rate-limit discovery alerts to avoid repeated beeps from the same candidate. Synthetic replay/demo must not unexpectedly produce live alerts.
- Run alert playback without blocking capture; define interaction with manual recording playback and Stop playback. Document avoiding audio feedback into the monitored input.
- Include settings/help updates and tests for event selection, suppression, output-device failures and uninterrupted capture before release.

## Completion criteria

The release has the exact requested About credit, persistent and consistent Light/Dark controls, approved branding with existing-data compatibility, playable discovered-tone recordings with configurable silence-based stopping, registration-key unlocking under an agreed edition policy, a documented compilation/protection decision, tested distributable artifacts and an honest statement of remaining reverse-engineering limits.


## Google Chat notifications — 0.8.17

Implemented October 10: standalone incoming-webhook destination format, auto URL recognition, multiline template/preview, transcript permission handling and existing FTP dependency/retry support. Setup in GOOGLE-CHAT.md. Live Google Workspace delivery remains a field test.
