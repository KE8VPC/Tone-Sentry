# Tone Sentry 0.8.3 — Settings Import

Settings now has Import settings beside Export settings. Stop monitoring, choose a Tone Sentry settings export, review the changes, then Apply import. Invalid formats and unsupported schema versions are rejected before changing settings. The existing Tone library importer for other applications is unchanged.

Tone sets (including weekly test schedules), detector/discovery options, recording options and destination lists are replaced. This receiver retains its identity, site name, input/gain, output device, appearance, encoder path, automatic deletion policy and coordination configuration. Imported destinations are disabled and FTP passwords omitted; review endpoints, machine-specific script paths and environment references before enabling them.

A complete local configuration backup is saved under backups before applying. If applying fails, the original configuration is restored. If runtime recovery fails too, the error directs you to restart with the restored disk configuration. Backups may contain private credentials. Recordings/history are not imported or removed, and existing jobs keep their destination snapshots.

The release remains unrestricted. Source validation covers round trips, invalid files/schema versions, identity and local-setting preservation, disabled destinations, password omission, rollback, and GUI review/apply. Windows packaged diagnostics are isolated and synthetic; field radio, remote providers and other operating systems remain acceptance work.
