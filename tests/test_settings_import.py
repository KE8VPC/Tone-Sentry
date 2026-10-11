import copy
import json
import pytest
from tonepage.config import defaults,save_config,load_config
from tonepage.ftp_credentials import export_settings
from tonepage.settings_import import prepare_import,apply_import


def write_export(tmp_path,data):
    path=tmp_path/'export.json'
    path.write_text(json.dumps(data),encoding='utf-8')
    return path


def test_roundtrip_preserves_receiver_and_disables_actions(tmp_path):
    current=defaults();source=defaults()
    source['site']='Other receiver';source['input']['device']=999
    source['recording']['retention_days']=1
    source['tones'][0]['agency']='Imported Fire'
    source['integrations']=[dict(id='ftp',kind='ftp',enabled=True,password_b64='c2VjcmV0')]
    before=copy.deepcopy(source)
    candidate,report=prepare_import(write_export(tmp_path,source),current)
    assert candidate['tones']==source['tones']
    assert candidate['recording']['retention_days']==current['recording']['retention_days']
    for key in ('site','instance_id','input','playback','coordination','coordinator','ui'):
        assert candidate[key]==current[key]
    assert not candidate['integrations'][0]['enabled']
    assert 'password_b64' not in candidate['integrations'][0]
    assert 'c2VjcmV0' not in report and 'Imported Fire' in report
    assert source==before
    restored,_=prepare_import(write_export(tmp_path,export_settings(candidate)),current)
    assert restored==candidate


@pytest.mark.parametrize('data',[{},[],dict(schema=999,tones=[],recording={},integrations=[]),dict(schema=1,tones='bad',recording={},integrations=[])])
def test_bad_import_leaves_settings_unchanged(tmp_path,data):
    current=defaults();save_config(tmp_path,current)
    before=(tmp_path/'config.json').read_bytes()
    with pytest.raises(ValueError):prepare_import(write_export(tmp_path,data),current)
    assert (tmp_path/'config.json').read_bytes()==before


def test_backup_and_rollback(tmp_path):
    current=defaults();save_config(tmp_path,current)
    candidate=copy.deepcopy(current);candidate['tones'][0]['agency']='Changed'
    calls=[]
    def apply(config):
        calls.append(config)
        save_config(tmp_path,config)
        if len(calls)==1:raise RuntimeError('synthetic restart failure')
    with pytest.raises(ValueError,match='restored'):apply_import(tmp_path,current,candidate,apply)
    assert load_config(tmp_path)==current
    backup=next((tmp_path/'backups').glob('*.json'))
    assert json.loads(backup.read_text())==current
    result=apply_import(tmp_path,current,candidate,lambda c:save_config(tmp_path,c))
    assert result!=backup and load_config(tmp_path)==candidate


def test_gui_import_review_does_not_apply_until_button(tmp_path,monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    source=defaults();source['tones'][0]['agency']='Reviewed Fire'
    path=write_export(tmp_path,source)
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path/'receiver')
    monkeypatch.setattr('tonepage.gui.filedialog.askopenfilename',lambda **_:str(path))
    monkeypatch.setattr('tonepage.gui.messagebox.showinfo',lambda *_,**__:None)
    errors=[]
    monkeypatch.setattr('tonepage.gui.messagebox.showerror',lambda *args,**_:errors.append(args))
    def children(widget):
        for child in widget.winfo_children():yield child;yield from children(child)
    try:
        original=copy.deepcopy(app.config)
        app.import_settings()
        assert app.config==original and not (app.home/'backups').exists()
        button=next(w for w in children(root) if isinstance(w,ttk.Button) and w.cget('text')=='Apply import')
        button.invoke()
        assert not errors,errors
        assert app.config['tones'][0]['agency']=='Reviewed Fire'
        assert app.config['instance_id']==original['instance_id']
        assert len(list((app.home/'backups').glob('*.json')))==1
    finally:app.close()
