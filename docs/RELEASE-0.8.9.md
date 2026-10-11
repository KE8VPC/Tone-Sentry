# Tone Sentry 0.8.9 development test release

Settings > Audio, detection & recording now offers Filename time zone: Local time
or UTC. Local time uses the computer's time zone at the recording start, including
daylight saving. Filename {offset} is a numeric offset such as -0400 in Local time
mode and UTC in UTC mode. New configurations default to Local time. Older saved
configurations and imported settings without this option retain UTC.

Overview is labeled Time (local), Recordings is labeled Start (local), and Discover
Tones is labeled Last seen (local). Filename date/time describes recording START;
a recording-complete Overview row describes completion, so the seconds can differ.
This is a clarity/preference change, not a correction to stored event timestamps.

Active recordings and queued work retain their captured encoder settings; legacy
queued work without a timezone setting uses UTC. Existing files are not renamed.
JSON epoch timestamps, scheduler time zones and notification time placeholders are
unchanged. {filename} and {filename_url} continue using the actual completed filename.
Saving while monitoring uses the existing quiet-boundary settings workflow.

Close the previous application before opening this build with the same data folder.
Existing users who want local filenames must select Local time and Save.
Development licensing remains unrestricted. See VALIDATION-0.8.9.txt for validation.
