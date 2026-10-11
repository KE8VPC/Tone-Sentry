# Legacy tone import

Imported from the supplied tones.cfg. Source remains unchanged. Only agency descriptions, tone frequencies, minimum durations and repeat intervals were copied. Recipients, email bodies, credentials and executable actions were excluded.

| Agency | A / long Hz | B Hz | Minimum A / B s | Repeat interval s |
|---|---:|---:|---|---:|
| Wapak FD/EMS | 419 | 618.0 | 0.5 / 0.5 | 60 |
| Buckland First Responders | 768 | 1699.0 | 0.5 / 0.5 | 60 |
| St Marys Twp FD | 408 | 328.0 | 0.5 / 0.5 | 60 |
| New Bremen EMS | 935 | 650.0 | 0.5 / 0.5 | 60 |
| Cridersville FD | 1516 | 596.0 | 0.5 / 0.5 | 60 |
| Wayne Twp FD-EMS | 634 | 650.0 | 0.5 / 0.5 | 60 |
| Minster FD | 2145 | 596.0 | 0.5 / 0.5 | 60 |
| Minster EMS | 2145 | 1697.0 | 0.5 / 0.5 | 60 |
| Spencerville FD | 586 | 812.0 | 0.5 / 0.5 | 60 |
| New Bremen FD | 2247 | 596.0 | 0.5 / 0.5 | 60 |
| Ft Loramie Ems | 338 | 376.0 | 0.5 / 0.5 | 60 |
| New Knoxville Ems | 1699 | 596.0 | 0.5 / 0.5 | 60 |
| St Marys FD/EMS | 349 | 365.0 | 0.5 / 0.5 | 60 |
| Botkins FD | 419 | 338.0 | 0.5 / 0.5 | 30 |
| CERT Pager Alert | 328 | 408.0 | 0.5 / 1.0 | 30 |
| Auglaize All call | 877.4 | 517.5 | 0.5 / 1.0 | 30 |
| Cridersville EMS | 1516 | Long | 5.0 / - | 60 |
| St Johns FD-EMS | 1613 | Long | 5.0 / - | 60 |
| Uniopolis FD-EMS | 2048 | Long | 5.0 / - | 60 |
| Perry Twp FD-EMS | 1000 | Long | 5.0 / - | 60 |

## Mapping notes

- Tone1: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone2: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone3: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone4: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone5: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone6: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone7: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone8: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone9: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone10: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone11: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone12: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone13: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone14: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone15: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Tone16: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Longtone1: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Longtone2: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Longtone3: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Longtone4: legacy record_delay=1s recorded for review; pre-roll preserves tones instead of discarding audio
- Imported tone lengths as minimum durations; maximum durations and frequency tolerances are proposed and need radio validation.
- Frequencies less than 5 Hz apart retain their original values but have overlapping tolerance bands; the other tone in the sequence must distinguish them.
- Mapped ignore_after to duplicate-action suppression seconds; verify behavior against your legacy version.
- Email recipients, message bodies, credentials and executable commands were neither copied nor activated.
- Per-tone cloud sharing is off. Review settings before enabling any external destination.
