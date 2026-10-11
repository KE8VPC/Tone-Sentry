# Tone Sentry 0.8.2 — recording links and flat FTP uploads

- FTP and FTPS now upload directly into the configured remote directory. No receiver-ID or recording-ID folders are appended. Existing remote folders/files are not moved.
- New local recording filenames replace whitespace with underscores. Existing filenames are preserved. `{filename}` returns the actual basename without replacing underscores or adding escaping.
- New `{filename_url}` works in the shared message templates and script arguments. It percent-encodes spaces and special characters for URLs while preserving underscores. Use `[Listen](https://example.com/audio/{filename_url})` in Discord, replacing the example website address with your own public audio URL. Use the exact placeholder spelling without spaces inside braces.
- Leave the FTP remote filename template blank or use `{filename}` to keep it consistent with links. A custom remote rename must also be reflected in the link template. FTP and webhook deliveries are independent: links become available after the audio upload finishes.
- Existing remote files are checked before retry acceptance. Different contents cause a collision error; matching files require read permission for byte verification. Servers without SIZE support fall back to a directory listing.

The source suite covers exact underscore preservation, URL encoding, real local plain FTP uploads into one folder, retry verification and same-size conflicting contents. Windows packaged diagnostics use synthetic audio and isolated data. Remote hosting, FTPS, physical radio, and other platforms still require operator acceptance.

Close the older version before launching this unrestricted Windows x64 development build. The 0.8.1 Base64 FTP password option and 0.8.0 data-folder migration remain included.
