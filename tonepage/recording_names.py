"""Persistent, collision-safe short filenames; recording identity stays unchanged."""
import json
import secrets
from pathlib import Path
from .storage_paths import managed_audio


def reserve_filename(store,folder,stem,recording_id):
    folder=Path(folder).resolve()
    key='recording-filename:'+recording_id
    with store.transaction() as db:
        previous=db.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
        if previous:
            target=Path(json.loads(previous[0]))
            if target.parent!=folder or not managed_audio(store.home,target):
                raise ValueError('Reserved recording filename is outside its audio folder')
            sidecar=target.with_suffix('.json')
            if sidecar.exists():
                if json.loads(sidecar.read_text(encoding='utf-8')).get('recording_id')!=recording_id:
                    raise ValueError('Reserved recording filename belongs to another recording; original WAV retained')
            elif target.exists():
                raise ValueError('Reserved recording metadata is missing; original WAV retained')
            else:
                with target.open('xb'):pass
                with sidecar.open('x',encoding='utf-8') as out:json.dump({'recording_id':recording_id,'status':'encoding'},out)
            return target
        # Recover a completed encode from an earlier version without renaming it.
        legacy=folder/(stem+'_'+recording_id+'.mp3')
        if legacy.is_file() and legacy.stat().st_size:
            db.execute('INSERT INTO kv VALUES(?,?)',(key,json.dumps(str(legacy))))
            return legacy
        for _ in range(100):
            target=folder/(stem+'_'+secrets.token_hex(3)+'.mp3')
            sidecar=target.with_suffix('.json')
            if sidecar.exists() or target.with_suffix('.part.mp3').exists():continue
            try:
                with target.open('xb'):pass
            except FileExistsError:continue
            try:
                with sidecar.open('x',encoding='utf-8') as out:
                    json.dump({'recording_id':recording_id,'status':'encoding'},out)
            except FileExistsError:
                target.unlink()  # Only our new empty reservation; never an existing recording.
                continue
            db.execute('INSERT INTO kv VALUES(?,?)',(key,json.dumps(str(target))))
            return target
    raise ValueError('Could not reserve a unique six-character recording filename; original WAV retained')


def filename_clock(stamp, mode='UTC'):
    """Format recording start using the OS local zone or UTC; never alter epoch data."""
    from datetime import datetime, timezone
    if mode not in ('Local time', 'UTC'):
        raise ValueError('Filename time zone must be Local time or UTC')
    dt = datetime.fromtimestamp(stamp, timezone.utc)
    if mode == 'Local time':
        dt = dt.astimezone()
    return {'date': dt.strftime('%Y-%m-%d'), 'time': dt.strftime('%H-%M-%S'),
            'offset': 'UTC' if mode == 'UTC' else dt.strftime('%z')}
