"""Read-only import adapters for other applications. No credentials/actions are activated."""
from __future__ import annotations

import configparser
import copy
import hashlib
import json
import math
import re
from pathlib import Path


def import_twotonedetect(path: Path, config: dict):
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read_string(path.read_text(encoding="utf-8-sig", errors="strict"))
    tones, notes = [], []
    for section in parser.sections():
        s = parser[section]
        if "longtone" in s:
            kind, a = "long", float(s["longtone"])
            amin = float(s.get("longtonelength", "3"))
        elif "atone" in s and "btone" in s:
            kind, a = "two", float(s["atone"])
            amin = float(s.get("atonelength", "0.5"))
        else:
            notes.append(f"{section}: no supported tone definition; skipped")
            continue
        ident = "ttd-" + re.sub(r"[^a-z0-9_-]", "-", section.lower())[:70]
        t = {"id": ident, "agency": s.get("description", section), "enabled": True,
             "kind": kind, "a_hz": a, "a_min": amin, "a_max": max(amin+2, 12 if kind == "long" else 5),
             "gap_max": 0.3, "tolerance_hz": 10.0, "duplicate_seconds": float(s.get("ignore_after", "120")),
             "tests": [], "allow_cloud": False}
        if kind == "two":
            t.update(b_hz=float(s["btone"]), b_min=float(s.get("btonelength", "0.5")))
            t["b_max"] = max(8, t["b_min"]+2)
        tones.append(t)
        if "record_delay" in s:
            notes.append(f"{section}: legacy record_delay={float(s['record_delay']):g}s recorded for review; pre-roll preserves tones instead of discarding audio")
    if not tones:
        raise ValueError("No two-tone or long-tone definitions found")
    frequencies = sorted({t[k] for t in tones for k in ("a_hz", "b_hz") if k in t})
    for t in tones:
        # Legacy rounded variants such as 1697/1699 Hz may represent the same
        # nominal tone. Do not imply reliable 2-Hz discrimination on radio audio;
        # their different A tones distinguish the configured sequences.
        distances = [abs(t[k]-other) for k in ("a_hz", "b_hz") if k in t for other in frequencies if abs(other-t[k]) >= 5]
        if distances:
            t["tolerance_hz"] = round(min(10., min(distances)*.4), 2)
        if t["kind"] == "two":
            t["tolerance_hz"] = min(t["tolerance_hz"], abs(t["a_hz"]-t["b_hz"])*.4)
    result = copy.deepcopy(config)
    result["tones"] = tones
    # Existing routes may reference replaced IDs. Disable rather than silently retarget.
    for d in result["integrations"]:
        if d.get("tone_ids"):
            d["enabled"] = False
            d["tone_ids"] = []
    notes += ["Imported tone lengths as minimum durations; maximum durations and frequency tolerances are proposed and need radio validation.",
              "Frequencies less than 5 Hz apart retain their original values but have overlapping tolerance bands; the other tone in the sequence must distinguish them.",
              "Mapped ignore_after to duplicate-action suppression seconds; verify behavior against your legacy version.",
              "Email recipients, message bodies, credentials and executable commands were neither copied nor activated.",
              "Per-tone cloud sharing is off. Review settings before enabling any external destination."]
    return result, notes


def import_fd_tone_notify(path: Path, config: dict):
    """Map the documented FD Tone Notify config/default.json contract.

    Its match counters are not continuous durations. Keep imported detectors
    disabled until the operator reviews the proposed seconds-based timing.
    """
    source = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(source, dict) or not isinstance(source.get("detection"), dict):
        raise ValueError("Expected an FD Tone Notify configuration with a detection section")
    detection, audio = source["detection"], source.get("audio", {})
    detectors = detection.get("detectors")
    if not isinstance(detectors, list):
        raise ValueError("The detection section must contain a detectors list")
    result = copy.deepcopy(config)
    notes, tones = [], []
    def numeric(value, name, low=0, high=86400):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {name}; expected a number between {low} and {high}")
        return float(value)
    if "sampleRate" in audio:
        rate = numeric(audio["sampleRate"], "sample rate", 8000, 48000)
        if rate not in (8000,16000,22050,24000,32000,44100,48000):
            raise ValueError("Source sample rate is not supported")
        result["input"]["sample_rate"] = int(rate)
    if "silenceAmplitude" in audio:
        rms = numeric(audio["silenceAmplitude"], "silence amplitude", .0001, 1)
        result["recording"]["silence_rms"] = rms
        result["detector"]["min_rms"] = rms
    if "inputDevice" in audio or "channels" in audio:
        notes.append("Select the audio device/channel in Settings: SoX/ALSA device identifiers do not map reliably to PortAudio devices.")
    for key in ("frequencyScaleFactor", "recordingScaleFactor"):
        if key in audio:
            notes.append(f"Audio {key} is not applied; the audio implementations use different scaling rules.")
    r = result["recording"]
    minimum = numeric(detection.get("minRecordingLengthSec", r["min_seconds"]), "minimum recording seconds", 0, 3500)
    maximum = numeric(detection.get("maxRecordingLengthSec", minimum*1.5), "maximum recording seconds", 1, 3600)
    if maximum <= minimum:
        maximum = min(3600, minimum*1.5+1)
        notes.append("Global maximum recording duration was increased to exceed the minimum.")
    r.update(min_seconds=minimum, max_seconds=maximum, fixed_seconds=0, pre_roll=min(r["pre_roll"], maximum/2))
    if isinstance(source.get("recording"), dict) and "autoDeleteOlderThanDays" in source["recording"]:
        r["retention_days"] = numeric(source["recording"]["autoDeleteOlderThanDays"], "retention days", 0, 36500)
        notes.append(f"Automatic purge age imported: {r['retention_days']:g} days (0 keeps files). Review in Scheduler before applying.")
    used_ids = set()
    for index, item in enumerate(detectors, 1):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError(f"Detector {index} needs a name")
        label = item["name"].strip()
        values = item.get("tones")
        if not isinstance(values, list) or not values:
            raise ValueError(f"{label}: tones must be a nonempty array")
        if len(values) not in (1,2):
            notes.append(f"SKIPPED {label}: {len(values)}-tone sequences are unsupported; only single long-tone and two-tone sequences can be imported.")
            continue
        values = [numeric(hz, f"{label} frequency", 100, 3500) for hz in values]
        frac = numeric(item.get("tolerancePercent", detection.get("defaultTolerancePercent", .05)), "frequency tolerance", 0, .5)
        if frac == 0:
            notes.append(f"SKIPPED {label}: zero frequency tolerance is unsupported; configure an explicit nonzero tolerance.")
            continue
        if len(values) == 2 and abs(values[0]-values[1]) <= sum(values)*frac:
            notes.append(f"SKIPPED {label}: the source A/B tolerance bands overlap; narrow them before importing.")
            continue
        stable = hashlib.sha256((label+":"+",".join(map(str,values))).encode()).hexdigest()[:12]
        ident = "fdtn-"+stable
        if ident in used_ids:
            notes.append(f"SKIPPED {label}: duplicate detector definition.")
            continue
        used_ids.add(ident)
        t = {"id":ident, "agency":label, "enabled":False, "kind":"two" if len(values)==2 else "long",
             "a_hz":values[0], "a_min":.5 if len(values)==2 else 3., "a_max":5. if len(values)==2 else 12.,
             "gap_max":.3, "tolerance_hz":max(1,min(100,values[0]*frac)), "tolerance_percent":frac,
             "duplicate_seconds":numeric(item.get("lockoutTimeoutMs", detection.get("defaultLockoutTimeoutMs",7000)), "lockout milliseconds",0,86400000)/1000,
             "tests":[], "allow_cloud":False,
             "record_enabled":item.get("isRecordingEnabled", detection.get("isRecordingEnabled",True))}
        if not isinstance(t["record_enabled"],bool):
            raise ValueError(f"{label}: isRecordingEnabled must be a boolean")
        if len(values)==2:
            t.update(b_hz=values[1],b_min=.5,b_max=8.)
        for source_key, target_key in (("minRecordingLengthSec","record_min_seconds"),("maxRecordingLengthSec","record_max_seconds")):
            if source_key in item:
                t[target_key] = numeric(item[source_key], label+" "+source_key, 0, 3600)
        tmin, tmax = t.get("record_min_seconds",minimum),t.get("record_max_seconds",maximum)
        if tmax <= max(tmin,r["pre_roll"]):
            t["record_max_seconds"] = min(3600,max(tmin*1.5+1,r["pre_roll"]+1))
            notes.append(f"{label}: maximum recording duration increased to keep it above minimum/pre-roll.")
        tones.append(t)
        threshold = numeric(item.get("matchThreshold", detection.get("defaultMatchThreshold",6)), "match threshold",1,10000)
        notes.append(f"{label}: matchThreshold={threshold:g} counts pitch estimates, not seconds. Proposed tone minimums {t['a_min']:g}s require review; imported disabled.")
    if not tones:
        raise ValueError("No compatible detectors found. " + " ".join(notes))
    result["tones"] = tones
    for destination in result["integrations"]:
        if destination.get("tone_ids"):
            destination["enabled"] = False
            destination["tone_ids"] = []
    notes += ["Frequency tolerance percentages are preserved per frequency; lockout milliseconds map to duplicate-action seconds.",
              "Reset timeouts and clarity thresholds are not converted to A/B gaps or spectral purity: those algorithms differ.",
              "Source recording paths, credentials, notification recipients, webhooks and external commands are not copied or activated. Configure destinations separately.",
              "Review the preview, then enable each imported tone set after confirming its duration limits."]
    return result, notes


def import_other_application(path: Path, config: dict):
    text = path.read_text(encoding="utf-8-sig").lstrip()
    if text.startswith("{"):
        return import_fd_tone_notify(path, config)
    return import_twotonedetect(path, config)
