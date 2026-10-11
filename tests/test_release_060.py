import json
import time
from pathlib import Path
import numpy as np
from tonepage.config import defaults, load_config
from tonepage.engine import Engine
from tonepage.store import Store
from tonepage.storage_paths import managed_audio
from tonepage.level_meter import dbfs


def test_clear_log_preserves_jobs_and_new_activity(tmp_path):
    s=Store(tmp_path)
    s.event('detection',{},event_id='one')
    assert s.clear_history('events')==1
    s.event('detection',{},event_id='two')
    assert [r['id'] for r in s.visible_history('events')]==['two']
    s.enqueue('sent','webhook',{})
    job=s.claim();s.finish(job)
    s.enqueue('pending','webhook',{})
    assert s.clear_history('jobs',True)==1
    assert [r['id'] for r in s.visible_history('jobs')]==['pending']
    s.enqueue('sent','webhook',{})
    assert s.rows("SELECT status FROM jobs WHERE id='sent'")[0]['status']=='done'
    s.close();s=Store(tmp_path)
    assert [r['id'] for r in s.visible_history('events')]==['two']
    s.close()


def test_new_audio_flat_layout_and_legacy_cleanup(tmp_path):
    e=Engine(tmp_path,defaults())
    try:
        e.begin_recording(time.time())
        assert e.active['path'].parent==tmp_path/'audio'
        e.finish_recording()
        legacy=tmp_path/'recordings'/'old-instance'/'old.mp3'
        legacy.parent.mkdir(parents=True);legacy.write_bytes(b'audio')
        legacy.with_suffix('.json').write_text('{}')
        e.store.recording('old',0,1,'complete',legacy,{})
        assert e.store.cleanup(1)==1 and not legacy.exists()
        assert managed_audio(tmp_path,tmp_path/'audio'/'one.mp3')
        assert not managed_audio(tmp_path,tmp_path/'audio'/'..'/'outside.mp3')
    finally:e.close();e.store.close()


def test_gain_applied_once_and_hardware_clipping_visible(tmp_path):
    c=defaults();c['input']['gain']=.5
    e=Engine(tmp_path,c)
    try:
        e.process(np.full(640,.8,dtype=np.float32))
        assert abs(e.level-.4)<.001 and abs(e.peak_level-.4)<.001
        e.process(np.ones(640,dtype=np.float32))
        assert e.overload_until>time.monotonic()
        assert dbfs(1)==0 and dbfs(0)==-60
    finally:e.close();e.store.close()


def test_live_gain_and_formatted_help(tmp_path):
    import tkinter as tk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        e=app.engine;e.running=True
        app.meter.set_gain(1.5);app.save_live_gain()
        assert app.engine is e and e.running
        assert load_config(tmp_path)['input']['gain']==1.5
        app.show_help()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        area=next(w for w in win.winfo_children() if isinstance(w,tk.Text))
        assert area.tag_cget('heading','underline')=='1'
        assert len(area.tag_ranges('heading'))>10
        assert 'AUDIO FILES AND HISTORY CONTROLS' in area.get('1.0','end')
    finally:e.running=False;app.close()


def test_destination_rename_keeps_internal_identity(tmp_path):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        original=dict(id='stable-id',name='Old label',kind='webhook',enabled=False,url='https://example.invalid/hook',triggers=['recording_complete'])
        app.config['integrations']=[original]
        app.edit_integration(original,lambda:None)
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        label=next(w for w in descendants(win) if isinstance(w,ttk.Label) and w.cget('text')=='Destination name')
        entry=label.master.grid_slaves(row=label.grid_info()['row'],column=1)[0]
        entry.delete(0,'end');entry.insert(0,'Wapak Discord')
        next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Save destination').invoke()
        saved=load_config(tmp_path)['integrations'][0]
        assert saved['id']=='stable-id' and saved['name']=='Wapak Discord'
        assert saved['url']==original['url'] and not saved['enabled']
    finally:app.close()
