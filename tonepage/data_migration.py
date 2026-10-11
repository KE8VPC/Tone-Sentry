"""Copy-and-verify migration of the legacy default; original data is retained."""
import json
import os
import shutil
import sqlite3
import stat
import uuid
from contextlib import ExitStack
from pathlib import Path
from .store import InstanceLock

MARKER='migration-from-legacy.json'
REDIRECT='moved-to-ToneSentryData.json'


def rewrite_paths(value, old, new):
    if isinstance(value,dict):return {k:rewrite_paths(v,old,new) for k,v in value.items()}
    if isinstance(value,list):return [rewrite_paths(v,old,new) for v in value]
    if isinstance(value,str):
        normalized=value.replace('\\','/')
        prefix=str(old).replace('\\','/')
        if normalized.casefold()==prefix.casefold():return str(new)
        if normalized.casefold().startswith(prefix.casefold()+'/'):
            return str(new/Path(normalized[len(prefix)+1:]))
    return value


def copy_database(source,target,old,new):
    src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    dest=sqlite3.connect(target)
    try:
        src.backup(dest)
        assert dest.execute('PRAGMA quick_check').fetchone()[0]=='ok','Database integrity check failed'
        tables=dest.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        for (name,) in tables:
            quoted='"'+name.replace('"','""')+'"'
            columns=[r[1] for r in dest.execute('PRAGMA table_info('+quoted+')')]
            for row in dest.execute('SELECT rowid,* FROM '+quoted).fetchall():
                updates={}
                for column,value in zip(columns,row[1:]):
                    if not isinstance(value,str):continue
                    try:
                        parsed=json.loads(value)
                        revised=rewrite_paths(parsed,old,new)
                        changed=json.dumps(revised) if revised!=parsed else value
                    except (ValueError,TypeError):changed=rewrite_paths(value,old,new)
                    if changed!=value:updates[column]=changed
                if updates:
                    setters=','.join('"'+col.replace('"','""')+'"=?' for col in updates)
                    dest.execute('UPDATE '+quoted+' SET '+setters+' WHERE rowid=?',(*updates.values(),row[0]))
        dest.commit()
        assert dest.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    finally:dest.close();src.close()


def prepare_default_home(lifetime,profile=None):
    profile=Path(profile or Path.home()).resolve()
    old=profile/'TonePageDetectData';new=profile/'ToneSentryData'
    # Serialize migration and default-folder selection across new launches.
    with ExitStack() as migration:
        gate=InstanceLock(profile,'.tonesentry-migration.lock');migration.callback(gate.close)
        if old.exists():
            marker=new/MARKER
            if new.exists() and not marker.exists():
                raise ValueError('Both ToneSentryData and TonePageDetectData exist. Select the intended folder with --home; neither was changed.')
            if new.exists():
                metadata=json.loads(marker.read_text(encoding='utf-8'))
                if metadata.get('source')!=str(old) or metadata.get('destination')!=str(new):
                    raise ValueError('Data migration marker does not match these folders; select a data folder explicitly.')
            for name in ('instance.lock','coordinator.lock'):
                lock=InstanceLock(old,name);lifetime.callback(lock.close)
            if new.exists():
                if not (new/'config.json').is_file():raise ValueError('Migrated settings are missing; original folder was retained for recovery.')
                if not (old/REDIRECT).exists():
                    (old/REDIRECT).write_text(json.dumps(metadata),encoding='utf-8')
                return new
            if (old/REDIRECT).exists():
                raise ValueError('Migrated ToneSentryData is missing. Restore that folder; the retained original may contain outdated delivery state.')
            if not (old/'config.json').is_file():raise ValueError('Legacy data folder has no config.json. Select a data folder with --home; nothing was migrated.')
            paths=list(old.rglob('*'))
            if any(p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT for p in [old]+paths):
                raise ValueError('Legacy data contains linked folders/files; use --home to keep using it until paths are reviewed.')
            required=sum(p.stat().st_size for p in paths if p.is_file())
            if shutil.disk_usage(profile).free<required+100*1024*1024:
                raise ValueError('Not enough free space to copy receiver data and retain the original. Use --home for the existing folder.')
            staging=profile/('ToneSentryData.migrating-'+uuid.uuid4().hex)
            staging.mkdir()
            # An interrupted staging folder is retained, never mistaken for a finished migration.
            for path in paths:
                relative=path.relative_to(old);target=staging/relative
                if path.name in ('instance.lock','coordinator.lock') or path.name.endswith(('.sqlite3-wal','.sqlite3-shm','.sqlite3-journal')):continue
                if path.is_dir():target.mkdir(exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                if path.suffix=='.sqlite3':copy_database(path,target,old,new)
                elif path.suffix=='.json':
                    value=json.loads(path.read_text(encoding='utf-8'))
                    target.write_text(json.dumps(rewrite_paths(value,old,new),indent=2),encoding='utf-8')
                else:shutil.copy2(path,target)
            from .config import load_config
            config=load_config(staging)
            original=json.loads((old/'config.json').read_text(encoding='utf-8'))
            if config['instance_id']!=original['instance_id']:raise ValueError('Receiver identity verification failed; original data was retained.')
            metadata=dict(source=str(old),destination=str(new),instance_id=config['instance_id'])
            (staging/MARKER).write_text(json.dumps(metadata),encoding='utf-8')
            staging.rename(new)
            (old/REDIRECT).write_text(json.dumps(metadata),encoding='utf-8')
        return new
