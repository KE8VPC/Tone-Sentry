from pathlib import Path
from tonepage.store import Store
from tonepage.engine import Engine
from tonepage.config import defaults


def test_external_delete_on_restart_then_clear(tmp_path):
    audio=tmp_path/'audio';audio.mkdir();path=audio/'page.mp3';path.write_bytes(b'audio')
    store=Store(tmp_path);store.recording('page',1,2,'complete',path,{})
    store.enqueue('upload','ftp',{'recording_id':'page'})
    store.close();path.unlink()
    engine=Engine(tmp_path,defaults())
    try:
        assert engine.store.recent('recordings')[0]['status']=='deleted'
        assert engine.store.clear_history('recordings',mode='deleted')==1
        assert not engine.store.visible_history('recordings')
        assert len(engine.store.recent('recordings'))==1
        assert len(engine.store.recent('jobs'))==1
    finally:engine.close();engine.store.close()


def test_clear_scans_legacy_and_skips_existing_active_and_unmanaged(tmp_path,monkeypatch):
    store=Store(tmp_path)
    paths={'legacy':tmp_path/'recordings'/'old'/'gone.mp3',
           'complete':tmp_path/'audio'/'present.mp3',
           'capturing':tmp_path/'audio'/'active.wav',
           'encoding':tmp_path/'audio'/'encode.wav',
           'outside':tmp_path/'outside.mp3',
           'denied':tmp_path/'audio'/'denied.mp3'}
    paths['complete'].parent.mkdir();paths['complete'].write_bytes(b'audio')
    for key,path in paths.items():store.recording(key,1,2,key if key in ('capturing','encoding') else 'complete',path,{})
    original=Path.stat
    def stat(path,*args,**kwargs):
        if path==paths['denied']:raise PermissionError('denied')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'stat',stat)
    try:
        assert store.clear_history('recordings',mode='deleted')==1
        assert {r['id'] for r in store.visible_history('recordings')}==set(paths)-{'legacy'}
        assert paths['complete'].read_bytes()==b'audio'
        assert store.reconcile_recordings()==0
    finally:store.close()
