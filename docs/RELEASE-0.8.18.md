# Tone Sentry 0.8.18

- Discovery clips now show confirmed page overlaps in desktop/web recordings and activity. Details link confirmed detections and normal recording IDs. Full candidate audio remains available for stacked-page review; no unknown tones are discarded or assumed identified.
- Optional Notify only beeps and independent discovery beeps through the selected playback device, with volume and unsent-settings audio preview. Manual playback has priority; output is asynchronous and rate-limited. Existing live dispatch listening is preserved.
- Existing monitoring, recording and external delivery settings remain unchanged. Close the old executable before using this version with the same data folder. New beep options are off until enabled.

Google Chat live acceptance is blocked by the user's account restrictions. The existing integration remains optional and locally tested. Transcription development is on hold pending a better model; no transcription work is included.


## Notify-only alerts and discovery recording context

In Playback device (also under Settings > Audio playback device), choose Known-tone listening mode: Off, Notify only, or Live dispatch audio. Existing live-audio settings are preserved on upgrade; new beep options start off. Notify only plays a short 880 Hz beep through the selected output. Alert volume is 0-100; use Preview alert tone to try the current unsaved output/volume. Save playback device to apply. Beeps do not enable/disable recording or external delivery and can be used for tone sets with recording disabled.

Beep for discovered tone candidates is a separate opt-in checkbox. It alerts on measured candidates, including candidates corresponding to known frequencies; it does not identify an agency. Repeated observations of a candidate beep at most once per 60 seconds, and all alerts share a two-second cooldown. Closely stacked notifications may therefore share one audible indication. Known-tone alerts honor duplicate and scheduled-test suppression. Safe demo/replay produces no alerts. Discovery has no agency identity, so agency-specific weekly-test rules do not suppress its beeps; turn discovery alerts off during those tests if desired.

Manual playback and active live-dispatch audio take priority over alerts. Stop playback cancels the current beep/session, but a later eligible event can alert again. Output errors appear in playback status and do not stop capture. Avoid feeding speaker audio back into the monitored receiver input. Verify the physical output device and comfortable volume on the receiver computer.

Discovery recordings are labeled Discovery clip - overlaps [agency] when confirmed detections overlap the clip, or Discovery clip - unconfirmed otherwise. The overlap label is advisory: it does not claim every tone belongs to that agency. Review the full sequence for unidentified tones in stacked pages. No clip or candidate is discarded, merged, automatically enabled or externally delivered by this feature.

Recording/event JSON details and Discover Tones candidate details include known_page_overlaps with confirmed event IDs, times, agencies and associated normal recording IDs where available. The desktop and web recordings/activity views show the context. Older clips can gain context if their detection history is still in this receiver database; clearing visible history does not remove it. Existing filenames and old JSON sidecar files are not renamed or rewritten. New discovery sidecars include overlaps known at encoding time; the application view can show later matches. Missing detection history means an unconfirmed label, not proof of an unknown agency.
