import sys
import json
import wave
from types import SimpleNamespace
import numpy as np
import pytest
from tonepage.config import defaults, load_config, validate
from tonepage.gain import GainControl
from tonepage.playback import Player, resolve_output
from tonepage.store import Store


def test_auto_gain_quiet_tones_overload_and_manual():
    gain=GainControl();settings={'gain':1.,'auto_gain':True}
    quiet=np.zeros(1600,dtype=np.float32)
    for _ in range(100):gain.process(quiet,16000,settings)
    assert gain.applied==1
    noise=np.random.default_rng(42).normal(0,.01,1600).astype(np.float32)
    for _ in range(100):gain.process(noise,16000,settings,.2,True)
    assert gain.applied==1
    tone=.03*np.sin(2*np.pi*1000*np.arange(1600)/16000).astype(np.float32)
    for _ in range(60):gain.process(tone,16000,settings,.99,True)
    assert 7<gain.applied<=8
    loud=gain.process(tone*30,16000,settings,.99,True)
    assert np.max(np.abs(loud))<=.501
    held=gain.applied
    for _ in range(100):gain.process(quiet,16000,settings)
    assert gain.applied==held
    assert np.allclose(gain.process(tone,16000,{'gain':2.,'auto_gain':False}),tone*2)


def test_clear_delivery_snapshots_persist_and_outcomes_return(tmp_path):
    store=Store(tmp_path)
    for key in ('cancelled','pending','completed'):store.enqueue(key,'webhook',{})
    with store.transaction() as db:
        db.execute("UPDATE jobs SET status='cancelled' WHERE id='cancelled'")
        db.execute("UPDATE jobs SET status='done' WHERE id='completed'")
    assert store.clear_history('jobs',mode='cancelled')==1
    assert store.clear_history('jobs',mode='all')==2
    assert store.clear_history('jobs',mode='all')==0
    store.close();store=Store(tmp_path)
    assert store.visible_history('jobs')==[]
    job=store.claim()
    assert [r['id'] for r in store.visible_history('jobs')]==['pending']
    store.clear_history('jobs',mode='all');store.finish(job)
    assert store.visible_history('jobs')[0]['status']=='done'
    store.enqueue('pending','webhook',{})
    assert len(store.recent('jobs'))==3
    store.close()


class AudioDevices:
    default=SimpleNamespace(device=(0,1))
    devices=[dict(name='Radio',hostapi=0,max_output_channels=0),
             dict(name='Headphones',hostapi=0,max_output_channels=2,default_samplerate=16000)]
    def query_hostapis(self):return [dict(name='Test audio')]
    def query_devices(self,index=None,kind=None):return self.devices if index is None else self.devices[index]


def test_output_identity_survives_indices_and_refuses_missing():
    sd=AudioDevices();selection=dict(name='Headphones',hostapi='Test audio')
    assert resolve_output(sd,None)[0]==1
    assert resolve_output(sd,selection)[0]==1
    sd.devices=list(reversed(sd.devices))
    assert resolve_output(sd,selection)[0]==0
    with pytest.raises(ValueError,match='unavailable'):resolve_output(sd,dict(name='Missing',hostapi='Test audio'))
    sd.devices=sd.devices+sd.devices
    with pytest.raises(ValueError,match='ambiguous'):resolve_output(sd,selection)


@pytest.mark.parametrize('invalid',[False,True])
def test_real_decoder_with_simulated_output(tmp_path,monkeypatch,invalid):
    sd=AudioDevices();written=[]
    class Stream:
        def __init__(self,**kwargs):assert kwargs['device']==1
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def write(self,data):written.append(data.copy())
        def abort(self):pass
    sd.OutputStream=Stream;sd.check_output_settings=lambda **kwargs:None
    monkeypatch.setitem(sys.modules,'sounddevice',sd)
    path=tmp_path/'audio.wav'
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes((np.sin(np.arange(16000)*.2)*10000).astype('<i2').tobytes())
    if invalid:path.write_bytes(b'invalid audio')
    config=defaults();config['playback']['device']=dict(name='Headphones',hostapi='Test audio')
    player=Player()
    try:
        player.play(path,config);player.thread.join(10)
        assert not player.thread.is_alive() and player.process is None
        if invalid:assert player.status.startswith('Playback error:') and not written
        else:assert player.status=='Playback finished' and sum(len(x) for x in written)==16000
    finally:player.close()


def test_shared_meters_and_saved_auto_mode(tmp_path):
    import tkinter as tk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        app.auto_gain.set(True);app.set_auto_gain()
        assert load_config(tmp_path)['input']['auto_gain']
        app.discovery_meter.set_gain(1.7);app.save_live_gain();app.refresh_meter()
        assert not app.auto_gain.get()
        assert app.discovery_meter.gain==app.meter.gain==1.7
        assert load_config(tmp_path)['input']['gain']==1.7
        assert len(app.discovery_meter.canvas.coords('gain_handle'))==10
        config=load_config(tmp_path);config['playback']['device']={'name':'Speakers','hostapi':'Test'};validate(config)
        config['playback']['device']='bad'
        with pytest.raises(ValueError):validate(config)
    finally:app.close()


def test_auto_gain_keeps_synthetic_page_results(tmp_path):
    from tonepage.engine import Engine
    from tonepage.demo import write_demo
    results=[]
    for auto in (False,True):
        home=tmp_path/str(auto);home.mkdir()
        config=defaults();config['input']['auto_gain']=auto
        config['discovery']['enabled']=True
        engine=Engine(home,config)
        try:
            engine.replay(write_demo(home/'demo.wav',config))
            results.append([(json.loads(row['data'])['tone_ids'],json.loads(row['data'])['duplicate']) for row in engine.store.recent('events') if row['type']=='detection'])
            assert engine.candidates.rows()
        finally:engine.close();engine.store.close()
    assert results[0]==results[1] and len(results[0])==3


def test_playback_can_stop_decoder(tmp_path,monkeypatch):
    sd=AudioDevices();player=Player();written=[]
    class Stream:
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def write(self,data):written.append(len(data));player.stop()
        def abort(self):written.append('aborted')
    sd.OutputStream=Stream;sd.check_output_settings=lambda **kwargs:None
    monkeypatch.setitem(sys.modules,'sounddevice',sd)
    path=tmp_path/'long.wav'
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(np.zeros(16000*60,dtype='<i2').tobytes())
    try:
        player.play(path,defaults());player.thread.join(10)
        assert not player.thread.is_alive() and player.process is None
        assert player.status=='Playback stopped' and written[-1]=='aborted'
        assert len(written)==2
    finally:player.close()


def test_playback_setting_saves_without_replacing_receiver(tmp_path,monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    monkeypatch.setitem(sys.modules,'sounddevice',AudioDevices())
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    try:
        engine=app.engine;input_before=dict(app.config['input'])
        app.playback_settings()
        window=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        combo=next(w for w in descendants(window) if isinstance(w,ttk.Combobox))
        combo.current(1)
        next(w for w in descendants(window) if isinstance(w,ttk.Button) and w.cget('text')=='Save playback device').invoke()
        assert load_config(tmp_path)['playback']['device']==dict(name='Headphones',hostapi='Test audio')
        assert app.engine is engine and app.config['input']==input_before
    finally:app.close()


def test_compact_window_keeps_lists_reachable(tmp_path):
    import tkinter as tk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        root.geometry('1020x690');root.deiconify();root.update()
        for name,tree in [('Overview',app.events_tree),('Discover Tones',app.candidate_tree)]:
            app.tabs.select(app.pages[name]);root.update()
            canvas=next(w for w in app.pages[name].winfo_children() if isinstance(w,tk.Canvas))
            assert tree.winfo_height()>200
            canvas.yview_moveto(1);root.update()
            assert tree.winfo_rooty()<canvas.winfo_rooty()+canvas.winfo_height()
            assert tree.winfo_rooty()+tree.winfo_height()<=canvas.winfo_rooty()+canvas.winfo_height()+1
    finally:app.close()
