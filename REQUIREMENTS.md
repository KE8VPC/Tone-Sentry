# Tone Page Detect requirements baseline

Implementation note: version 0.1.0 is now built. This document preserves the full intended design; see [release status](docs/RELEASE-STATUS.md) for implemented behavior, verified tests, and deferred extensions.

## Purpose and requested scope

Monitor live audio from a radio receiver, recognize configured public service paging tones, and record dispatch audio as MP3 files. Supported agency categories include fire, EMS, EMA, CERT, and all-call groups.

The application must operate locally without requiring a hosted service. Network access is needed only for configured remote transfers, external integrations, and optional multi-instance coordination. Core detection and recording must continue offline. Prefer one portable application distribution using an installed runtime, rather than requiring separate native application packages. Python and Java are under consideration; the language is not yet selected. The runtime and any native audio/MP3 dependencies must match the target operating system and processor architecture. Self-contained native bundles can be an optional later delivery format.

Requested capabilities:

- Windows, Linux, macOS, and ARM compatibility. ARM is a processor architecture; the release matrix must name specific OS and architecture combinations.
- Select an audio input connected to a radio source.
- Configure multiple named tone sets and their agency associations.
- Initial paging formats are two-tone sequential (A followed by B) and single long-tone paging, as confirmed by the user. Frequencies and timing thresholds are configurable per tone set.
- Record detected dispatches as MP3 files.
- Configure FTP transfers, automatic deletion after a chosen number of days, and filename conventions.
- Optionally execute a locally configured script for a matching tone set.
- Ignore scheduled weekly test pages.
- Detect stacked pages addressing multiple agencies in one dispatch sequence.
- Suppress duplicate actions for repeated pages, including second and third attempts.
- Allow optional third-party integrations for audio-to-text transcription, outgoing webhooks, and other API destinations through an extensible adapter interface. Providers are not yet selected.
- Support multiple cooperating receiver instances, including remote sites, to improve coverage and provide redundancy while preventing conflicting file writes and coordinating duplicate external actions.

## Proposed behavior requiring field validation

The following details are design proposals, not confirmed user settings or claims of implemented behavior.

### Audio input and detector

Continuously capture the selected sound device and maintain an in-memory pre-roll buffer. Device sample rate, channel selection, input gain, and detector settings must be configurable. Show signal level, clipping, device connection, and monitoring status.

Each tone set has a stable ID, display name, agency or agencies, enabled state, tone format, frequencies, duration ranges, allowed inter-tone gaps, frequency tolerance, and minimum signal-quality thresholds. Implement two-tone sequential and single long-tone detection initially. Do not assume all-call always uses a distinct single-tone format. Obtain actual frequencies, timing requirements, and representative audio for validation.

Keep device capture independent from detection, MP3 encoding, file transfers, and script execution so a slow destination or script cannot stop monitoring. Report audio discontinuities and device loss explicitly; reconnect when feasible.

### Events, stacked pages, and recording

Keep three separate concepts: a tone detection, an agency activation, and a dispatch recording session. Several detections and agency activations can belong to one recording session.

When an eligible tone set matches, start a recording with pre-roll or attach the detection to an active recording. Subsequent agency tone sets within a configurable stacking window join the same dispatch session. Preserve the ordered tone detections and their timestamps.

Use a single MP3 master per local recording session, with metadata listing every associated agency. In coordinated mode, preserve each receiver's original and associate those local sessions with a shared event; a preferred recording does not replace the other originals. Optional per-agency output copies can be added if required. Decide agency-based final filenames only after session membership is known. Allow transfer and script rules per tone set without inadvertently transferring identical content multiple times to the same destination.

End recordings using configurable post-roll and silence rules, with a maximum duration and continuation behavior for prolonged traffic. Offer fixed-duration recording if the radio feed's noise or squelch makes silence detection unreliable. Define silence from measured audio level, not missing tone detections.

### Duplicate suppression

Use a configurable suppression interval per tone set, scoped to the monitored input. A repeat of agency A must never suppress a first activation of agency B.

By default, repeats suppress additional script execution and duplicate agency notifications, while recording continues or extends as appropriate. Retain repeat detections in metadata. If a repeat arrives after the recording closes, preserve it as a linked follow-up recording under the proposed default instead of silently losing speech.

Anchor the suppression interval to the first accepted activation rather than extending it indefinitely with every repeat. Specify whether duplicate state persists across restarts; persistent timestamps are the proposed default.

Tone-only input cannot reliably distinguish a re-page from a separate incident for the same department. Expose this tradeoff in the suppression settings and allow suppression to be disabled or overridden. Recording suppression and action suppression must be separate controls.

### Weekly test-page exclusions

Configure schedules per tone set using named time zones, weekdays, local start times, and window lengths. Handle windows crossing midnight and daylight-saving changes explicitly.

Proposed default: a test-window match is logged but does not independently start a recording or run a script. Do not remove it from audio already being recorded. An eligible agency in a mixed stack must still trigger normal recording.

Offer a record-only test mode. A schedule alone cannot distinguish a real emergency page from a test inside the same window, so show that consequence beside the setting.

### File naming and metadata

Provide a filename template with preview and validation. Candidate tokens include date, time, UTC offset, agency, agency list, tone-set ID, input name, site ID, instance ID, session ID, and shared event ID when assigned. Use filesystem-safe substitutions on all supported systems. Prevent path traversal and silent overwrites; handle reserved names, collisions, and path-length limits. Coordinated storage must enforce an instance/session namespace even when the display template omits these tokens.

Store machine-readable session metadata containing timestamps, agency associations, detections, duplicate/test classifications, recording parts, and action outcomes. Store timestamps in UTC with enough timezone information for display and naming.

### Transfers and retention

Implement the requested FTP destination settings and upload queue. Consider FTPS and SFTP as additional destination types; they are distinct protocols. Keep credentials out of logs and exported settings by default.

Only queue finalized MP3 files. Use temporary remote filenames followed by rename where supported, retry failed jobs with backoff, and persist queue state across restarts. Show pending, successful, and failed transfers.

Retention uses a configurable number of days from recording completion. Proposed default: protect active recordings and files awaiting required transfers. Explain that this can exceed the selected retention period while a destination is unavailable. Define handling for permanent transfer failures and low disk space; never let silent disk exhaustion become the retention strategy.

Delete only files owned and tracked by this application inside configured recording roots. Decide metadata retention independently from audio retention.

### Per-tone script execution

Make execution opt-in for each tone set. Select an executable or script and explicit arguments, with supported event variables. Avoid constructing shell command strings from agency labels or filenames.

Offer activation-time and recording-complete triggers. A finalized MP3 path is available only for recording-complete triggers. Apply duplicate and test policies before dispatching actions. Enforce timeouts and concurrency limits; record exit codes and bounded output.

Persist action status. A process crash can make external side effects ambiguous; use a stable event ID for script-side deduplication and avoid promising exactly-once execution.

### Local operation and interface

Provide a desktop interface for input selection, tone sets, test schedules, recording settings, destinations, scripts, integrations, and retention. Show live status, recent detections, recordings, transcripts, integration jobs, and failures. Include configuration backup/restore and a sample-audio diagnostic/replay mode.

A background service or headless mode is a proposed addition for unattended receivers, especially Linux ARM installations. Keep the monitoring engine separate from the desktop interface so closing or reopening settings does not interrupt capture.

### Multi-instance detection, redundancy, and coverage

Support standalone mode and an optional coordinated receiver group. All receiver nodes actively detect and record, so a remote node can capture a page missed at another site. Coordination governs shared event association and external actions, not permission to receive audio.

#### Instance identity and registration

Assign each installation a persistent unique instance ID, a user-facing site name, and unique input IDs. Use a separate process-session ID on startup. Detect a second local process attempting to use the same data directory and prevent concurrent access using an OS-managed lock. Independent local instances require separate data directories and input configurations.

Remote instances explicitly enroll with a configured coordinator endpoint and group credentials. Registration and periodic heartbeats expose connected, stale, disconnected, and conflicting identities; do not assume remote instances can be discovered across the internet automatically. Cloning an installation must generate a new instance identity before group enrollment. Concurrent use of one instance identity must raise a conflict and suspend coordinated writes/actions for that identity while preserving local capture in isolated storage.

The coordinator is an optional self-hosted role that may run with one installation or on a separate machine. Begin with one authoritative coordinator and durable event/action storage. Coordinator high availability is a later extension requiring an authoritative shared state and an explicit failover design; a missing heartbeat alone must not authorize competing coordinators.

#### Matching observations across receivers

Configure coverage groups representing receivers monitoring the same paging system or known linked channels. Map local tone sets to shared agency and tone-set IDs with configuration revisions. Identical tone frequencies on unrelated systems must not cause event merging.

Keep each observation immutable and identify it with instance ID plus a unique local observation ID. Submit occurrence time, receipt time, input/coverage group, tone sequence and durations, agency mapping, configuration revision, and available quality measurements. Use UTC for correlation and monotonic elapsed time for local detector timing; report clock offset/uncertainty and allow configured transport delays.

Correlate the same transmitted page heard by multiple receivers separately from later dispatcher re-pages. Use a bounded cross-receiver time window, compatible tone signatures and coverage groups; optional audio similarity can strengthen a match. Tone names or timestamp buckets alone are insufficient. Ambiguous matches remain separate and reviewable. A shared event is a correlation result, not proof that two pages concern one real-world incident.

Combine agency associations when one receiver hears only part of a stacked page. A page heard by only one node remains eligible; do not require a majority of receivers. Late observations update an existing shared event when sufficiently supported instead of creating a new notification automatically. Preserve revisions and source attribution for added agencies and recording alternatives. Define a bounded reconciliation horizon and an operator-visible late-arrival policy; old observations do not trigger fresh alerts by default.

#### File isolation and recording quality

Each receiver owns its local database, recording directory, and upload spool. Do not share a writable local database or active MP3 file between installations, including through synchronized folders. Shared remote storage uses immutable per-instance/session object names, content checksums for transfer integrity, and unique temporary upload names. Independent recordings of the same transmission need not have identical checksums.

Allow the coordinator to select a preferred completed recording using measured tone quality, clipping, dropouts, speech coverage, and configurable site preference. Preserve alternatives and the reason for selection. Prefer a complete intelligible recording over a louder but clipped one. Keep automatic audio splicing outside initial scope; several source recordings may be linked to cover different portions of a dispatch.

A bounded recording-selection wait may improve transcription input without delaying the initial activation notification. Late better audio can be marked preferred, but retranscription or repeat delivery requires an explicit update policy. Sharing restrictions apply to the selected recording and every associated agency; a later agency association must not bypass those restrictions.

Retention runs only against a node's owned files. Shared archive cleanup has one designated owner and its own policy; one receiver cannot delete another's recording or remove a canonical file still referenced by pending work.

#### Shared actions, failover, and disconnected operation

In coordinated mode, the coordinator creates durable logical action keys from the shared event, agency where applicable, event revision/trigger, destination, and action type. Use transactional uniqueness and expiring worker claims with increasing ownership tokens to prevent concurrent scheduling and reject stale acknowledgments. Dispatch shared notifications, transcription, archive publication, and shared scripts through coordinator-controlled workers. Receivers do not independently run the same shared action.

Declare script/action scope explicitly: local-per-receiver actions may run at each site; shared actions run through the coordination queue. Keep local recording and raw archive-copy jobs distinct from canonical publication. Check action ownership before external dispatch, while recognizing that a worker may crash after a destination accepts a request. Reuse destination idempotency keys where supported; show ambiguous outcomes for non-idempotent scripts/APIs instead of assuming retries are harmless.

Default disconnected behavior: continue local detection/recording and durably spool observations, but defer shared actions until the coordinator is reachable. This favors duplicate prevention and can delay notifications. Offer an explicit availability-first policy allowing isolated nodes to send fallback actions; label those with node/event identities and acknowledge that duplicates can occur during a network partition. Never promise both uninterrupted independent external delivery and guaranteed global duplicate suppression while coordination is unavailable.

On reconnection, replay observations idempotently, associate delayed recordings, and reconcile action receipts. Previously sent fallback actions must be considered before scheduling further delivery. A coordinator outage does not authorize a node to overwrite shared files, erase peer state, or silently promote itself to a competing authority.

#### Coordination interface and visibility

Use an authenticated, encrypted coordination protocol with enrollment, revocation, group isolation, and version compatibility checks. Nodes connect outbound to the configured endpoint; general remote script execution or unrestricted administration is not implied by enrollment. Shared configuration changes are explicit and versioned; conflicting tone mappings are surfaced rather than silently overwritten.

Show each site's last heartbeat, audio-device status, clock health, pending observations/uploads, current connectivity, and contribution to shared events. Identify which sites heard a page and which recording was selected. Missing detections at a site can guide placement but do not establish a geographic coverage boundary without field measurements.

### Optional third-party API integrations

Integrations are optional and disabled until configured. Define a common adapter interface so transcription providers, webhook destinations, and other API connectors can be added without modifying tone detection. Specific vendors, pricing, account requirements, and API contracts must be evaluated against current provider documentation when selected; this baseline makes no promise of compatibility with a named service.

Configure integration rules globally and per agency or tone set, including destination, event trigger, allowed data fields, credentials, timeouts, retry limits, and whether a pending job protects its source recording from retention deletion. Apply weekly-test and duplicate-action policies before queuing external actions. An integration failure must never block audio capture or local MP3 recording.

#### Audio-to-text

Initially submit finalized dispatch recordings to a configured transcription API asynchronously. Keep streaming transcription as a possible later option. Allow a local/offline transcription adapter as a future alternative, subject to device performance and model availability.

Store transcript text alongside the recording and session metadata, with provider/model identifiers, processing status, and segment timestamps or confidence values only where returned by the provider. Preserve the original audio. Display machine-generated text as such and allow corrections while retaining the original result. Do not treat transcription as verified dispatch information or use it to override tone-based agency matching automatically.

Expose language and supported vocabulary hints, input-size/duration limits, concurrency controls, usage tracking, and a configurable local submission budget. Local budget controls limit submissions; they do not guarantee the provider's final bill. Avoid duplicate submissions for the same recording content, provider, model, and settings; allow an explicit reprocess action. Transcribe a shared stacked-page recording once per selected transcription configuration rather than once per agency.

Cloud transcription uploads audio. Make that choice explicit in settings and honor per-agency sharing rules. A shared stacked recording may contain several agencies' traffic: if any associated agency disallows sharing with a destination, hold that entire recording and derived transcript from that destination by default. Do not assume audio can be safely separated by agency. Local deletion does not imply deletion at a third-party provider; remote deletion, if available, requires a separately defined policy.

#### Outgoing webhooks

Support configurable HTTP POST webhooks with JSON payloads for eligible agency activation, recording completion, transcript completion, and selected operational failures. An activation event identifies the agency known at that moment; recording-complete events include the final stacked agency list. A transcript-complete event follows separately when transcription is enabled. Do not delay activation delivery while waiting for audio or transcription.

Use a versioned event envelope with a stable event ID, session ID, event type, occurrence timestamp, input ID, relevant agency/tone-set IDs, and duplicate/test classifications. Include recording metadata, transcript text, or a remote recording URL only when available and enabled for that destination. A local filesystem path is not a remotely accessible audio URL. Do not publish recordings automatically; URLs require an explicitly configured accessible destination and access policy.

Support destination authentication headers and optional HMAC signatures with timestamps. Use HTTPS for external destinations, protect stored credentials, redact secrets from logs, and never forward credentials automatically to a redirected host. Provide a payload preview and an explicit test-send action with clearly marked synthetic data.

Persist delivery jobs across restarts. Retry transient failures with bounded exponential backoff and jitter, honor provider rate-limit instructions, and surface permanent failures for inspection and manual retry. Reuse the same event ID and payload for delivery retries so recipients can deduplicate. Delivery may occur more than once; do not promise exactly-once effects or delivery order. Track per-destination outcomes and prevent recursive failure-webhook loops.

#### Additional connector possibilities

Candidate extensions include messaging/notification gateways, incident-management or CAD systems with documented authorized APIs, remote recording archives, and automation platforms that accept webhooks. These are extension points, not committed vendor integrations. Use stable session/event IDs to associate updates with an existing external incident where the destination supports it.

Keep general-purpose incoming webhooks and remote administration APIs out of the initial integration scope. The optional authenticated receiver-coordination endpoint is a separate, narrowly scoped feature defined above.

## Architecture outline

Audio capture -> bounded audio buffer -> tone detectors -> event coordinator -> recording sessions.

The event coordinator applies test schedules, groups stacked activations, and classifies repeats. Encoding and file finalization feed durable transfer, transcription, and recording-complete action queues. Activation actions use their own queue. Integration workers deliver webhooks and other API requests outside the audio-processing path; successful transcription emits a separate transcript-complete event. Retention operates only against tracked files and queue state, including protected integration inputs. A local settings and event store supports restart recovery and the desktop interface.

Implementation language, UI framework, audio library, and MP3 encoder remain undecided. The distribution preference is one portable application with an installed runtime. Python can share source across targets but audio libraries may require native components; Java can share a JAR across compatible JVMs, with audio and MP3 support still requiring verification on each target. Verify current dependencies and licensing before selecting them.

In coordinated mode, node event stores feed durable observation spools into the group coordinator. The coordinator correlates observations into shared events, selects recording references, and owns shared integration scheduling. Local capture remains independent. The coordination protocol, storage backend, and deployment details remain design decisions to validate before implementation.

## Platform decisions needed

- Windows and Linux x64 are candidate desktop targets.
- macOS Apple Silicon and Linux ARM64 are candidate ARM targets.
- Confirm whether Windows ARM64, Intel macOS, or Linux 32-bit ARM are also required.
- Name any Raspberry Pi or other embedded target and its operating system.
- Confirm whether a USB/line-in sound device is sufficient initially or whether network audio sources and multiple concurrent inputs are required.

## Delivery stages

1. Select the portable runtime and target hardware; obtain representative two-tone and long-tone audio and known tone settings.
2. Build and validate an offline decoder/replay harness with synthetic signals and labeled recordings.
3. Add live capture, recording sessions, stacked-page handling, duplicate policy, and schedule handling.
4. Add MP3 finalization, naming, durable transfers, retention, and optional scripts.
5. Add the integration adapter interface, outgoing webhooks, and a selected transcription provider; validate failure recovery and per-agency sharing policies.
6. Add multi-instance registration, observation correlation, isolated storage, shared action ownership, and disconnected recovery; validate with multiple simulated and physical receivers.
7. Add desktop configuration and operational status; distribute the shared application with platform-specific dependency instructions and test each supported OS/architecture combination.

## Acceptance criteria

- Recognize configured tone sequences across specified frequency, duration, gap, and signal-level boundaries; reject speech and out-of-range near matches in the test corpus.
- Preserve pre-roll and dispatch audio, produce playable MP3s, and report capture gaps.
- A stack for agencies A, B, and C produces one shared session with all three associations and one eligible activation per agency.
- Repeated A pages suppress duplicate actions while preserving audio under the selected recording policy; they do not suppress B.
- A subsequent A detection outside its suppression interval produces a new eligible activation.
- Weekly exclusions behave correctly across timezone changes, daylight-saving transitions, midnight boundaries, and mixed test/non-test stacks.
- Filename collisions and invalid template input cannot overwrite files or escape recording roots.
- Slow or unavailable transfer destinations and hanging scripts cannot stall audio capture.
- Interrupted transfers recover through persisted queue state without presenting partial uploads as complete.
- Retention cannot remove active files, unrelated files, or protected pending-transfer files.
- Device disconnection, application restart, low disk space, and encoder failure produce visible status and defined recovery behavior.
- With all integrations disabled or the network unavailable, tone detection and local recording continue normally.
- Transcription errors, timeouts, rate limits, invalid responses, and exhausted submission budgets produce explicit job status without losing the local recording.
- A shared stacked recording is transcribed once per selected configuration; blocked agency sharing policies prevent disallowed audio and transcript uploads.
- Webhook retries preserve event IDs and payloads across restarts; duplicate/test suppression prevents unintended new external actions.
- Activation, recording-complete, and transcript-complete payloads contain only data available at that stage and allowed for their destination.
- Required integration jobs protect their source audio from deletion; terminal failures have an explicit resolution policy so files are not silently retained forever.
- Credentials are absent from logs, payload previews, and default configuration exports. Failed webhook delivery cannot cause recursive failure notifications.
- Each claimed platform receives native installation, capture, detection, recording/playback, and restart smoke tests. Source portability alone does not prove platform support.
- A second process cannot open an active instance data directory; cloned/conflicting identities are detected without stopping isolated local capture.
- Two enrolled receivers hearing the same transmission retain separate recordings and produce one logical shared action per configured destination/trigger; unrelated coverage groups are never merged merely for matching tones.
- A page heard at only one site produces an eligible shared event, and complementary stacked-page observations preserve all supported agency associations.
- Clock skew, input latency, ambiguous matches, repeat transmissions, and late observations exercise documented matching boundaries without silently combining unrelated calls.
- Concurrent uploads, identical display filenames, interrupted writes, and node retention cannot overwrite or delete another instance's data.
- Coordinator/worker crashes and stale ownership claims preserve queue consistency; ambiguous external side effects are visible and tested with idempotent and non-idempotent destinations.
- During a network partition, default mode records locally and defers shared delivery; availability-first mode explicitly permits traceable fallback duplicates. Reconnection replays observations without scheduling already-known actions again.
- Better late recordings can update the preferred source without automatically repeating transcription or notifications. Source identity and sharing restrictions remain attached to every recording and transcript.
- Revoked or wrong-group nodes cannot submit observations or claim shared work; configuration conflicts and incompatible protocol versions produce visible status.
