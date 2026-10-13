from __future__ import annotations

import copy
import json
import math
import os
import re
import string
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def default_home() -> Path:
    if os.name == "nt":
        # Windows packaged hosts can redirect AppData. An explicit profile folder
        # keeps normal desktop and packaged-host launches on the same identity.
        return Path.home() / "ToneSentryData"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "tone-page-detect"


def defaults() -> dict:
    from .discovery_recording import AUDIO_DEFAULTS
    return {
        "schema": 1, "instance_id": str(uuid.uuid4()), "site": "Receiver 1",
        "ui": {"theme": "Light", "start_monitoring": False},
        "input": {"device": None, "channel": 0, "sample_rate": 16000, "gain": 1.0, "auto_gain": False},
        "playback": {"device": None, "live_after_detection": False, "notify_after_detection": False, "discovery_alert": False, "alert_volume": 30},
        "detector": {"frame_ms": 40, "min_rms": 0.015, "min_purity": 0.65},
        "discovery": {"enabled":False,"min_seconds":.5,"long_seconds":2.,"max_seconds":15.,
                      "gap_seconds":.5,"stability_hz":8.,"min_purity":.85,"dropout_seconds":.08, **AUDIO_DEFAULTS},
        "recording": {"pre_roll": 8, "post_roll": 4, "silence_seconds": 8,
                      "min_seconds": 12, "max_seconds": 180, "fixed_seconds": 0,
                      "silence_rms": 0.012, "stack_seconds": 20, "retention_days": 30,
                      "filename": "{date}_{time}_{agencies}", "filename_timezone": "Local time", "bitrate": "64k", "ffmpeg": ""},
        "tones": [
            {"id": "demo-fire", "agency": "DEMO Fire", "enabled": True, "kind": "two",
             "a_hz": 600.0, "b_hz": 900.0, "a_min": 0.8, "a_max": 1.5,
             "b_min": 2.5, "b_max": 4.0, "gap_max": 0.3, "tolerance_hz": 15,
             "duplicate_seconds": 120, "tests": [], "allow_cloud": False},
            {"id": "demo-all", "agency": "DEMO All Call", "enabled": True, "kind": "long",
             "a_hz": 1000.0, "a_min": 3.0, "a_max": 8.0, "gap_max": 0.3,
             "tolerance_hz": 15, "duplicate_seconds": 120, "tests": [], "allow_cloud": False},
        ],
        "integrations": [],
        "coordination": {"enabled": False, "url": "", "token_env": "TONEPAGE_GROUP_TOKEN",
                         "group": "default", "coverage": "dispatch-channel-1", "heartbeat_seconds": 10},
        "coordinator": {"bind": "127.0.0.1", "port": 8766,
                        "token_env": "TONEPAGE_GROUP_TOKEN", "match_seconds": 2.0,
                        "max_age_seconds": 300, "selection_wait_seconds": 5,
                        "allowed_instances": [], "revoked_instances": []},
    }


def merge(base: dict, changes: dict) -> dict:
    result = copy.deepcopy(base)
    for k, v in changes.items():
        result[k] = merge(result[k], v) if isinstance(v, dict) and isinstance(result.get(k), dict) else copy.deepcopy(v)
    return result


def number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be a number between {low} and {high}")


TOKENS = {"date", "time", "agency", "agencies", "site", "instance", "session", "offset"}
from .message_templates import FIELDS as DISCORD_FIELDS, validate_template


def validate_discord_template(template):
    if not isinstance(template,str) or not template.strip() or len(template)>2000:
        raise ValueError('Discord message template must contain 1–2000 characters')
    for _,field,spec,conversion in string.Formatter().parse(template):
        if field is not None and (field not in DISCORD_FIELDS or spec or conversion):
            raise ValueError('Unsupported Discord placeholder: '+str(field))
    return template


def validate(c: dict) -> dict:
    if type(c.get('ui', {}).get('start_monitoring', False)) is not bool:
        raise ValueError('Start monitoring on startup must be a checkbox value')
    if c.get('ui', {}).get('theme', 'Light') not in ('Light', 'Dark'):
        raise ValueError('Theme must be Light or Dark')
    if type(c['input'].get('auto_gain',False)) is not bool:
        raise ValueError('Auto gain must be a checkbox value')
    if type(c.get('playback',{}).get('live_after_detection',False)) is not bool:
        raise ValueError('Live dispatch playback must be a checkbox value')
    playback = c.get('playback', {})
    for field in ('notify_after_detection', 'discovery_alert'):
        if type(playback.get(field, False)) is not bool:
            raise ValueError('Audible notification options must be checkbox values')
    if playback.get('notify_after_detection') and playback.get('live_after_detection'):
        raise ValueError('Choose either Notify only or Live dispatch audio')
    number(playback.get('alert_volume', 30), 'Alert volume', 0, 100)
    output=c.get('playback',{}).get('device')
    if output is not None and (not isinstance(output,dict) or set(output)!={'name','hostapi'} or not all(isinstance(v,str) and v.strip() for v in output.values())):
        raise ValueError('Choose a playback device from the device list')
    uuid.UUID(c["instance_id"])
    if c["schema"] != 1:
        raise ValueError("Unsupported configuration schema")
    i, r, d = c["input"], c["recording"], c["detector"]
    if r.get("filename_timezone", "UTC") not in ("Local time", "UTC"):
        raise ValueError("Filename time zone must be Local time or UTC")
    discovery=c.get('discovery',{})
    number(discovery.get('dropout_seconds',.08),'Discovery dropout seconds',0,.3)
    number(discovery.get('min_hz',100.),'Discovery minimum frequency',100,3499)
    number(discovery.get('max_hz',3500.),'Discovery maximum frequency',101,3500)
    if discovery.get('min_hz',100.)>=discovery.get('max_hz',3500.):
        raise ValueError('Discovery minimum frequency must be below maximum frequency')
    from .discovery_recording import AUDIO_DEFAULTS
    audio = dict(AUDIO_DEFAULTS, **discovery)
    if type(audio['record_enabled']) is not bool:
        raise ValueError('Record discovered candidates must be a checkbox value')
    for key, low, high in [('audio_pre_roll',0,30), ('audio_silence_seconds',.2,60), ('audio_silence_rms',.0001,1), ('audio_min_seconds',0,600), ('audio_post_roll',0,60), ('audio_max_seconds',5,3600)]:
        number(audio[key], 'Discovery '+key, low, high)
    if audio['audio_max_seconds'] <= max(audio['audio_min_seconds'], audio['audio_pre_roll']+discovery.get('min_seconds',.5)+.3):
        raise ValueError('Discovery maximum audio duration must exceed minimum duration and pre-roll buffer')
    if audio['audio_silence_seconds'] <= discovery.get('gap_seconds',.5):
        raise ValueError('Discovery audio silence must exceed the allowed gap between tones')
    if type(discovery.get('enabled',False)) is not bool:
        raise ValueError('Discovery enabled must be a checkbox value')
    for key,low,high,default in [('min_seconds',.12,10,.5),('long_seconds',.5,30,2.),('max_seconds',1,60,15.),('gap_seconds',0,5,.5),('stability_hz',1,30,8.),('min_purity',.1,1,.85)]:
        number(discovery.get(key,default),'Discovery '+key,low,high)
    if discovery.get('max_seconds',15)<max(discovery.get('min_seconds',.5),discovery.get('long_seconds',2.)):
        raise ValueError('Discovery maximum duration must cover minimum and long-tone durations')
    if i["sample_rate"] not in (8000, 16000, 22050, 24000, 32000, 44100, 48000):
        raise ValueError("Unsupported sample rate")
    number(i["channel"], "Input channel", 0, 31)
    if int(i["channel"]) != i["channel"]:
        raise ValueError("Input channel must be an integer")
    number(i["gain"], "Gain", 0.01, 100)
    number(d["frame_ms"], "Frame duration", 20, 100)
    number(d["min_rms"], "Minimum signal", 0.0001, 1)
    number(d["min_purity"], "Tone purity", 0.1, 1)
    for k in ("pre_roll", "post_roll", "silence_seconds", "min_seconds", "max_seconds", "fixed_seconds", "stack_seconds"):
        number(r[k], k, 0, 3600)
    if r["max_seconds"] <= max(r["pre_roll"], r["min_seconds"], r["fixed_seconds"]):
        raise ValueError("Maximum recording duration must exceed pre-roll, minimum and fixed durations")
    number(r["retention_days"], "Retention days (0 disables cleanup)", 0, 36500)
    number(r["silence_rms"], "Silence level", 0, 1)
    if not re.fullmatch(r"(32|48|64|96|128|192)k", r["bitrate"]):
        raise ValueError("Unsupported MP3 bitrate")
    for _, field, spec, conversion in string.Formatter().parse(r["filename"]):
        if field is not None and (field not in TOKENS or spec or conversion):
            raise ValueError(f"Unsupported filename token: {field}")
    ids = set()
    for t in c["tones"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", t["id"]) or t["id"] in ids:
            raise ValueError("Tone IDs must be unique letters, digits, dashes or underscores")
        ids.add(t["id"])
        if not t["agency"].strip() or t["kind"] not in ("two", "long"):
            raise ValueError("Each tone needs an agency and kind two/long")
        for key in (["a"] if t["kind"] == "long" else ["a", "b"]):
            number(t[f"{key}_hz"], "Frequency", 100, min(3500, i["sample_rate"] / 2 - 100))
            number(t[f"{key}_min"], "Minimum tone duration", 0.12, 30)
            number(t[f"{key}_max"], "Maximum tone duration", t[f"{key}_min"], 60)
        number(t["gap_max"], "Tone gap", 0, 5)
        number(t["tolerance_hz"], "Frequency tolerance", 1, 100)
        number(t["duplicate_seconds"], "Duplicate window", 0, 86400)
        frac = t.get("tolerance_percent")
        if frac is not None:
            number(frac, "Frequency tolerance fraction", .0001, .5)
        combined = (t["a_hz"]+t.get("b_hz",0))*frac if frac is not None else 2*t["tolerance_hz"]
        if t["kind"] == "two" and abs(t["a_hz"] - t["b_hz"]) <= combined:
            raise ValueError("A/B frequency tolerance bands must not overlap")
        if not isinstance(t.get("record_enabled",True),bool):
            raise ValueError("Record dispatch audio must be enabled or disabled")
        for key in ("record_min_seconds","record_max_seconds"):
            if key in t:
                number(t[key],key,0,3600)
        if t.get("record_max_seconds",r["max_seconds"]) <= max(t.get("record_min_seconds",r["min_seconds"]),r["pre_roll"]):
            raise ValueError(f"{t['agency']}: maximum recording duration must exceed minimum and pre-roll")
        for s in t.get("tests", []):
            if not isinstance(s.get("enabled",True),bool):
                raise ValueError("Schedule enabled must be a checkbox value")
            ZoneInfo(s["timezone"])
            datetime.strptime(s["start"], "%H:%M")
            number(s["minutes"], "Test window minutes", 1, 1440)
            if not isinstance(s["days"],list) or not s["days"] or any(type(day) is not int or day not in range(7) for day in s["days"]):
                raise ValueError("Schedule weekdays use Monday=0 through Sunday=6")
            if s.get("mode", "ignore") not in ("ignore", "record_only"):
                raise ValueError("Test mode must be ignore or record_only")
    dest_ids = set()
    for dest in c["integrations"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", dest["id"]) or dest["id"] in dest_ids:
            raise ValueError("Integration IDs must be unique and filesystem-safe")
        dest_ids.add(dest["id"])
        if dest["kind"] not in ("webhook", "ftp", "ftps", "script", "transcription", "email"):
            raise ValueError("Unsupported integration kind")
        if dest.get('webhook_format', 'auto') not in ('auto', 'generic', 'discord', 'google_chat'):
            raise ValueError('Webhook format must be auto, generic, discord or google_chat')
        if dest['kind']=='webhook':
            validate_discord_template(dest.get('discord_template','{agency} - {time}'))
            validate_template(dest.get('google_chat_template','{agency} - {time}'))
            if dest.get('webhook_format') == 'google_chat' and dest.get('enabled'):
                from .integrations import is_google_chat_webhook
                if not is_google_chat_webhook(dest.get('url','')):
                    raise ValueError('Google Chat requires the complete HTTPS space webhook URL, including key and token')
        for field in ('webhook_template','email_subject_template','email_body_template','remote_filename_template'):
            if field in dest:validate_template(dest[field],allow_empty=True)
        if any(ch in dest.get('email_subject_template','') for ch in '\r\n'):
            raise ValueError('Email subject template must be one line')
        if dest.get("scope", "shared") not in ("shared", "local"):
            raise ValueError("Integration scope must be shared or local")
        if set(dest.get("tone_ids", [])) - ids:
            raise ValueError("Integration references unknown tone IDs")
        if dest['kind']=='script' and dest.get('script_file') and (not isinstance(dest['script_file'],str) or not dest['script_file'].strip() or any(c in dest['script_file'] for c in '\r\n\0')):
            raise ValueError('Choose a valid script file path')
        if dest["kind"] == "script" and not dest.get('script_file') and (not isinstance(dest.get("argv"), list) or not dest["argv"]):
            raise ValueError("Script argv must be a nonempty list")
        triggers = dest.get("triggers", ["recording_complete"])
        if not isinstance(triggers, list) or set(triggers) - {"activation", "recording_complete", "transcript_complete"}:
            raise ValueError("Integration triggers must be activation, recording_complete or transcript_complete")
        if dest["kind"] in ("transcription", "ftp", "ftps", "email") and triggers != ["recording_complete"]:
            raise ValueError("Transcription, FTP and email destinations run on recording_complete only")
        if dest['kind']=='email':
            if dest.get('smtp_security','starttls') not in ('starttls','ssl'):
                raise ValueError('Email SMTP security must be starttls or ssl')
            number(dest.get('smtp_port',587),'SMTP port',1,65535)
            number(dest.get('email_max_mb',15),'Email attachment size limit MB',1,100)
            recipients=dest.get('recipients',[])
            if not isinstance(recipients,list): raise ValueError('Email recipients must be a list')
            for address in recipients+([dest['email_from']] if dest.get('email_from') else []):
                if not isinstance(address,str) or not re.fullmatch(r'[^\s@<>,;]+@[^\s@<>,;]+\.[^\s@<>,;]+',address):
                    raise ValueError('Enter one plain email address per recipient, without display names')
            if any(ch in dest.get('email_subject','') for ch in '\r\n'):
                raise ValueError('Email subject must be one line')
            if dest.get('enabled') and (not dest.get('smtp_host','').strip() or not dest.get('email_from') or not recipients):
                raise ValueError('Enabled email requires SMTP host, sender and at least one recipient')
            if dest.get('enabled') and dest.get('smtp_username') and not dest.get('smtp_password_env'):
                raise ValueError('Authenticated SMTP needs a password environment variable name')
        if dest["kind"] == "transcription":
            number(dest.get("daily_limit", 100), "Daily submission limit", 0, 100000)
            number(dest.get("max_bytes", 25000000), "Transcription file size limit", 1024, 100000000)
        if dest["kind"] == "script":
            number(dest.get("timeout", 30), "Script timeout", 1, 300)
    number(c["coordinator"]["match_seconds"], "Receiver match window", 0.1, 10)
    number(c["coordinator"]["max_age_seconds"], "Late alert limit", 10, 86400)
    for dest in c['integrations']:
        dependency=dest.get('wait_for_ftp','')
        if dependency:
            upload=next((d for d in c['integrations'] if d['id']==dependency),None)
            if dest['kind']!='webhook' or dest.get('triggers',['recording_complete'])!=['recording_complete']:
                raise ValueError('Wait for FTP is available for Recording complete webhooks only')
            if not upload or upload['kind'] not in ('ftp','ftps'):
                raise ValueError('Choose an existing FTP or FTPS destination to wait for')
            if upload.get('scope','shared')!=dest.get('scope','shared'):
                raise ValueError('Webhook and required FTP upload must use the same delivery scope')
    number(c["coordinator"]["selection_wait_seconds"], "Recording selection delay", 0, 300)
    number(c["coordinator"]["port"], "Coordinator port", 1, 65535)
    for key in ("allowed_instances", "revoked_instances"):
        for instance in c["coordinator"].get(key, []):
            uuid.UUID(instance)
    number(c["coordination"]["heartbeat_seconds"], "Heartbeat interval", 2, 300)
    return c


def save_config(home: Path, c: dict):
    validate(c)
    home.mkdir(parents=True, exist_ok=True)
    temp = home / "config.json.tmp"
    temp.write_text(json.dumps(c, indent=2), encoding="utf-8")
    temp.replace(home / "config.json")


def load_config(home: Path) -> dict:
    path = home / "config.json"
    if not path.exists():
        save_config(home, defaults())
    incoming = json.loads(path.read_text(encoding="utf-8"))
    incoming.setdefault("recording", {}).setdefault("filename_timezone", "UTC")
    return validate(merge(defaults(), incoming))


def test_mode(tone: dict, timestamp: float) -> str | None:
    for s in tone.get("tests", []):
        if not s.get("enabled",True):
            continue
        local = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(ZoneInfo(s["timezone"]))
        hour, minute = map(int, s["start"].split(":"))
        # Wall-clock windows deliberately cover both occurrences of an ambiguous DST hour.
        wall = local.replace(tzinfo=None)
        for back in (0, 1):
            start = (wall - timedelta(days=back)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            if start.weekday() in s["days"] and start <= wall < start + timedelta(minutes=s["minutes"]):
                return s.get("mode", "ignore")
    return None


def safe_name(value: str) -> str:
    value = re.sub(r"[^\w .+-]", "_", str(value), flags=re.UNICODE).strip(" .")[:100]
    if not value or value.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{x}" for x in range(1, 10)), *(f"LPT{x}" for x in range(1, 10))}:
        value = "_" + value
    return value
