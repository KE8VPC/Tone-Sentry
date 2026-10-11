"""Reviewable settings imports; receiver-local settings stay on this computer."""
import copy
import json
import uuid
from datetime import datetime
from pathlib import Path
from .config import defaults, merge, validate, save_config


def prepare_import(path, current):
    path=Path(path)
    if path.stat().st_size>2_000_000:
        raise ValueError('Settings file is too large (maximum 2 MB)')
    try:
        incoming=json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(incoming,dict) or type(incoming.get('schema')) is not int or incoming.get('schema')!=1:
            raise ValueError()
        if not all(key in incoming for key in ('tones','recording','integrations')):
            raise ValueError()
        incoming["recording"].setdefault("filename_timezone", "UTC")
        candidate=merge(defaults(),incoming)
        # These are machine/receiver bindings, not transferable preferences.
        for key in ('instance_id','site','input','playback','ui','coordination','coordinator'):
            candidate[key]=copy.deepcopy(current[key])
        candidate['recording']['ffmpeg']=current['recording'].get('ffmpeg','')
        candidate['recording']['retention_days']=current['recording']['retention_days']
        for destination in candidate['integrations']:
            destination['enabled']=False
            destination.pop('password_b64',None)
        validate(candidate)
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError):
        raise ValueError('This is not a valid supported Tone Sentry settings export. Check the file and its version; current settings have not changed.') from None
    changed=[key for key in candidate if candidate[key]!=current.get(key)]
    report=[f'Tone sets: {len(current["tones"])} → {len(candidate["tones"])}',
            f'Destinations: {len(current["integrations"])} → {len(candidate["integrations"])}',
            'Changed sections: '+(', '.join(changed) or 'none'),
            'Tone sets: '+(', '.join(str(t['agency']) for t in candidate['tones']) or 'none'),
            '', 'Imported tone sets, schedules and destinations replace the existing lists.',
            'This receiver keeps its identity, site name, audio input/gain, playback device, appearance, encoder path, automatic deletion policy and coordination settings.',
            'All imported destinations will be disabled. Review their addresses, paths, scripts and credential references before enabling them. Saved FTP passwords are not imported; enter them again.',
            'Recordings, history and existing queued jobs are not imported or removed. Existing jobs keep their original settings.',
            'A full local settings backup is saved before applying. It can contain private credentials.']
    return candidate,'\n\n'.join(report)


def apply_import(home, current, candidate, apply):
    validate(candidate)
    backup_dir=Path(home)/'backups'
    backup_dir.mkdir(exist_ok=True)
    backup=backup_dir/('settings-before-import-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.json')
    with backup.open('x',encoding='utf-8') as output:
        json.dump(current,output,indent=2)
    try:
        apply(copy.deepcopy(candidate))
    except Exception:
        save_config(Path(home),current)
        try:
            apply(copy.deepcopy(current))
        except Exception:
            raise ValueError('Import failed. Original settings were restored on disk. Close and reopen Tone Sentry before continuing.') from None
        raise ValueError('Import failed; the original settings were restored.') from None
    return backup
