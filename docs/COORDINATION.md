# Redundant receiver setup

Every receiver captures locally. An optional single authoritative coordinator associates observations and queues shared actions. Nodes never share writable databases or active MP3 files.

## Enrollment

1. Choose a coordinator machine/data directory and run `python -m tonepage --home /absolute/coordinator-data init`.
2. Import the same tone IDs and frequencies used by the receivers. Configure shared destinations in this coordinator configuration; node-specific destinations use `scope: local`.
3. Set the token environment variable to a randomly generated secret of at least 24 characters, shared only with enrolled operators.
4. Run `python -m tonepage --home /absolute/coordinator-data coordinator`.
5. For remote access, place the loopback-bound server behind HTTPS with a valid certificate. Forward only `/heartbeat`, `/observe`, and `/recording`, enforce a 30 MB request limit, and apply appropriate connection/rate limits. Public deployment has not been performed or audited in this build.
6. At each receiver, configure the HTTPS URL, token variable, group and coverage name under Receivers → Configure receiver connection.

An empty `coordinator.allowed_instances` accepts UUIDs held by group-token users. Populate it to restrict enrollment. `revoked_instances` denies listed UUIDs; rotate the token if disclosed. One endpoint serves one configured group.

Fresh installations have independent UUIDs. Run `new-identity` after cloning settings onto another receiver. Concurrent use of one UUID with a different process session produces a conflict. Normal restart may wait up to 45 seconds for the previous heartbeat to expire; local recording continues.

## Association and audio

The same tone set heard by different receivers within `match_seconds` (default 2 seconds) can share an event when group, coverage and signature match. Another observation from the same receiver is treated as a later transmission. New agencies within the stacking window may join. Multiple plausible matches remain separate.

The coordinator applies its own test schedules and persistent repeat window. One receiver is sufficient; no majority vote is required. Observations older than `max_age_seconds` (default 300) are archived without new activation notifications. Synchronize clocks externally: observed clock offset is displayed, but automatic correction and input-delay calibration are not implemented.

Nodes durably submit observations before uploading their completed recordings. Enrollment permits copying audio into the trusted group archive. Maximum recording upload is 20 MB; SHA-256 and immutable source/recording IDs prevent conflicting replacements. Originals remain at the nodes.

After `selection_wait_seconds` (default 5 seconds from the first candidate), the coordinator chooses by reported quality score. This score combines spectral tone purity, clipping fraction and an interruption penalty; it is a proxy, not measured speech intelligibility. Alternatives remain available. Later better audio updates the preferred reference without automatically repeating a completed notification or transcription. Automatic audio splicing is not implemented.

## Shared actions and outages

Stable action keys and transactional queue claims prevent competing local workers from scheduling the same logical action. One coordinator process owns the database; distributed leader election and remote worker leasing are not included.

Implemented outage mode favors duplicate prevention: continue recording, spool observations, and defer shared external actions. Reconnection resumes idempotent observation replay and uploads. Nodes never silently promote themselves or send shared fallback notifications. Availability-first independent fallback remains a future option.

Heartbeat responses populate the Receivers roster. The coordinator `status` command lists nodes, shared events and jobs. No geographic coverage boundary is inferred automatically.

Tone/time association remains heuristic and cannot prove real incident identity. Field-test overlapping and non-overlapping sites and inspect missed detections/false merges before relying on coordinated suppression operationally.

