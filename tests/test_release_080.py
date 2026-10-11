import json
import re
from contextlib import ExitStack
from pathlib import Path
import pytest
from tonepage.config import defaults,load_config,save_config,validate
from tonepage.store import Store,InstanceLock
from tonepage.data_migration import prepare_default_home
from tonepage.recording_names import reserve_filename
from tonepage.message_templates import filename_for,render


def test_migration_preserves_identity_audio_jobs_and_paths(tmp_path):
    old=tmp_path/'TonePageDetectData';old.mkdir()
    config=defaults();save_config(old,config)
    audio=old/'audio'/'historic.mp3';audio.parent.mkdir();audio.write_bytes(b'ID3-original')
    metadata=dict(recording_id='record',path=str(audio))
    audio.with_suffix('.json').write_text(json.dumps(metadata))
    store=Store(old);store.recording('record',1,2,'complete',audio,metadata)
    store.enqueue('pending','ftp',dict(event=metadata))
    store.set('recording-filename:record',str(audio));store.close()
    with ExitStack() as lifetime:
        new=prepare_default_home(lifetime,tmp_path)
        assert load_config(new)['instance_id']==config['instance_id']
        copied=new/'audio'/'historic.mp3'
        assert copied.read_bytes()==audio.read_bytes()
        assert json.loads(copied.with_suffix('.json').read_text())['path']==str(copied)
        store=Store(new)
        assert store.recent('recordings')[0]['path']==str(copied)
        assert json.loads(store.recent('jobs')[0]['payload'])['event']['path']==str(copied)
        assert store.recent('jobs')[0]['status']=='pending'
        assert store.get('recording-filename:record')==str(copied)
        store.close()
        with pytest.raises(RuntimeError):InstanceLock(old)
    with ExitStack() as lifetime:assert prepare_default_home(lifetime,tmp_path)==new
    original=Store(old)
    assert original.recent('recordings')[0]['path']==str(audio)
    original.close()


def test_migration_refuses_two_independent_folders_or_active_receiver(tmp_path):
    old=tmp_path/'TonePageDetectData';save_config(old,defaults())
    lock=InstanceLock(old)
    try:
        with ExitStack() as stack,pytest.raises(RuntimeError):prepare_default_home(stack,tmp_path)
        assert not (tmp_path/'ToneSentryData').exists()
    finally:lock.close()
    save_config(tmp_path/'ToneSentryData',defaults())
    with ExitStack() as stack,pytest.raises(ValueError,match='Both'):prepare_default_home(stack,tmp_path)


def test_failed_migration_never_publishes_partial_data(tmp_path,monkeypatch):
    import tonepage.data_migration as migration
    old=tmp_path/'TonePageDetectData';save_config(old,defaults());store=Store(old);store.close()
    real=migration.copy_database
    def fail(*args):raise OSError('simulated copy failure')
    monkeypatch.setattr(migration,'copy_database',fail)
    with ExitStack() as stack,pytest.raises(OSError):prepare_default_home(stack,tmp_path)
    assert not (tmp_path/'ToneSentryData').exists() and (old/'config.json').is_file()
    assert list(tmp_path.glob('ToneSentryData.migrating-*'))
    monkeypatch.setattr(migration,'copy_database',real)
    with ExitStack() as stack:assert prepare_default_home(stack,tmp_path).is_dir()


def test_explicit_home_does_not_migrate(tmp_path,monkeypatch):
    from tonepage.cli import main
    def forbidden(*args):raise AssertionError('Explicit home must not migrate')
    monkeypatch.setattr('tonepage.data_migration.prepare_default_home',forbidden)
    assert main(['--home',str(tmp_path/'custom'),'init'])==0
    assert (tmp_path/'custom'/'config.json').is_file()


def test_short_filename_collision_and_restart(tmp_path,monkeypatch):
    root=tmp_path/'audio';root.mkdir()
    existing=root/'Page_abcdef.mp3';existing.write_bytes(b'original')
    ids=iter(['abcdef','123abc'])
    monkeypatch.setattr('tonepage.recording_names.secrets.token_hex',lambda size:next(ids))
    store=Store(tmp_path)
    target=reserve_filename(store,root,'Page','full-recording-uuid')
    assert target.name=='Page_123abc.mp3' and existing.read_bytes()==b'original'
    assert json.loads(target.with_suffix('.json').read_text())['recording_id']=='full-recording-uuid'
    store.close();store=Store(tmp_path)
    assert reserve_filename(store,root,'Changed template','full-recording-uuid')==target
    store.close()


def test_shared_filename_templates_and_webhook_privacy(tmp_path):
    from tonepage.integrations import queue_actions,webhook_payload
    config=defaults();config['integrations']=[dict(id='web',kind='webhook',enabled=True,url='https://example.invalid/hook',webhook_template='{site}: {filename}')]
    event=dict(id='one',type='recording_complete',recording_id='one',site='Beam',path=r'C:\private\audio\Page_123abc.mp3',agencies=['Fire'])
    store=Store(tmp_path);queue_actions(store,config,event)
    queued=json.loads(store.recent('jobs')[0]['payload'])['event']
    assert 'path' not in queued and queued['filename']=='Page_123abc.mp3'
    assert webhook_payload(config['integrations'][0],queued)['message']=='Beam: Page_123abc.mp3'
    assert webhook_payload(dict(webhook_format='discord',discord_template='{filename}'),queued)['content']=='Page_123abc.mp3'
    assert filename_for(dict(event,type='activation'))==''
    assert render('File: {filename}',dict(type='activation'))=='File: '
    assert render('{filename}',dict(event,type='transcript_complete'))=='Page_123abc.mp3'
    with pytest.raises(ValueError):render('{filename.__class__}',event)
    store.close()


def test_email_and_script_filename_templates(tmp_path,monkeypatch):
    from tonepage.integrations import JobWorker
    store=Store(tmp_path);config=defaults();worker=JobWorker(store,config)
    path=tmp_path/'audio'/'Page_123abc.mp3';path.parent.mkdir();path.write_bytes(b'ID3')
    event=dict(id='one',type='recording_complete',recording_id='one',site='Beam',agencies=['Fire'],path=str(path))
    captured=[]
    class SMTP:
        def __init__(self,*args,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def ehlo(self):pass
        def starttls(self,context):pass
        def send_message(self,message,**kwargs):captured.append(message);return {}
    monkeypatch.setattr('tonepage.integrations.smtplib.SMTP',SMTP)
    dest=dict(smtp_host='example.invalid',email_from='a@example.invalid',recipients=['b@example.invalid'],email_subject_template='{site} - {filename}',email_body_template='File: {filename}')
    worker.execute(dict(id='email',kind='email',payload=dict(destination=dest,event=event)))
    assert captured[0]['Subject']=='Beam - Page_123abc.mp3'
    assert 'File: Page_123abc.mp3' in captured[0].get_body().get_content()
    commands=[]
    from types import SimpleNamespace
    monkeypatch.setattr('tonepage.integrations.subprocess.run',lambda argv,**kwargs:commands.append(argv) or SimpleNamespace(returncode=0))
    worker.execute(dict(id='script',kind='script',payload=dict(destination=dict(argv=['test-only','{filename}']),event=event)))
    assert commands==[['test-only','Page_123abc.mp3']]
    store.close()


@pytest.mark.parametrize('scaling',[1.3333,1.6667,2.0])
def test_header_and_meter_fit_small_screen(tmp_path,scaling):
    # Each DPI case gets a fresh native Tcl interpreter/process. Repeated Tk
    # teardown and scaling changes in one Windows process can corrupt theme loading.
    import subprocess,sys
    script="import runpy,sys; from pathlib import Path; runpy.run_path(sys.argv[1])['_check_header_and_meter_fit'](Path(sys.argv[2]),float(sys.argv[3]))"
    result=subprocess.run([sys.executable,'-c',script,str(Path(__file__).resolve()),str(tmp_path),str(scaling)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr


def _check_header_and_meter_fit(tmp_path,scaling):
    import tkinter as tk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();root.tk.call('tk','scaling',scaling)
    app=Application(root,tmp_path)
    try:
        root.deiconify()
        for size in ('1020x690','880x460'):
            root.geometry(size);root.update()
            buttons=[item[0] for item in app.header_buttons]
            assert len({b.winfo_rooty() for b in buttons})==1
            assert all(b.winfo_width()>=b.winfo_reqwidth() for b in buttons)
            assert buttons[-1].winfo_rootx()+buttons[-1].winfo_width()<=root.winfo_rootx()+root.winfo_width()
        assert app.meter.winfo_reqheight()<110
        for theme in ('Light','Dark'):
            app.change_theme(theme)
            from tkinter import ttk
            for state in (('selected',),('!selected',)):
                assert tuple(map(int,root.tk.splitlist(ttk.Style(root).lookup('TNotebook.Tab','padding',state))))==(4,6)
            for page in app.pages.values():app.tabs.select(page);root.update()
        app.engine.running=True;app.update_monitor_label()
        assert 'Stop' in app.start_button.cget('text')
    finally:app.engine.running=False;app.close()
