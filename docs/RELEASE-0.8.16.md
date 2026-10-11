# Tone Sentry 0.8.16 — overnight web-console reliability update

- Fix a Windows windowed-EXE listener crash: rejected TLS certificates or other
  connection errors previously invoked Cheroot logging on missing stderr. Logging
  now creates throttled, sanitized local events without terminating the listener.
- Unexpected listener failures include their exception type in Settings and in
  Overview. Open current web console reports a stopped listener instead of trying
  to open its error text as a URL.
- Web setup displays local IPv4 addresses with adapter names and connection state.
  Refresh local IPs updates the reference. Look up public IP explicitly contacts
  api.ipify.org in a background worker, validates the reply and reports offline
  failures. No automatic public-IP lookup, listener change or firewall change.
- Successful web sign-ins appear once in Overview, showing account name, connecting
  IP and receiver-local date/time. Routine browser polling does not create notices.
  No passwords or session tokens appear in those events.
- Reset gain, Auto gain and Save meter are side by side on Overview and Discover
  Tones. Their functions and radio processing are unchanged.

## Upgrade and overnight test

Close the old EXE, launch the new one, and keep the existing ToneSentryData folder.
Saved tones, destinations, recordings and web accounts remain in place. Web access
uses its saved enabled setting. Monitoring starts automatically only if that
preference is enabled; otherwise click Start monitoring.

For the reported test receiver, if its address is still 192.168.12.165:

- Settings → Remote web console → Listen address: **0.0.0.0**
- Receiver IP or hostname: **192.168.12.165**
- HTTPS port: **6124**
- Keep existing accounts by leaving username/password blank; Save and apply.
- Open **https://192.168.12.165:6124/** on the other device. Changing the browser
  hostname changes the generated certificate; compare its SHA-256 with Settings
  before accepting the first-visit certificate warning.

Close the setup dialog before trying remote control or tone edits. A successful
sign-in should create a Web sign in entry in Overview. For passive overnight
testing, leave the receiver monitoring and use Status/Recordings in the browser.
Closing the browser leaves monitoring running. Closing Tone Sentry ends web access.
Use a private LAN/VPN; firewall permissions may need adjustment on the receiver.

See WEB-CONSOLE.md and VALIDATION-0.8.16.txt for setup and validation scope.
