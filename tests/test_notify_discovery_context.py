import json
import time
import threading
import numpy as np
import pytest
from tonepage.config import defaults, validate
from tonepage.engine import Engine
from tonepage.detector import Detection
from tonepage.store import Store
from tonepage.discovery_context import context, label
from tonepage.alert_audio import AlertAudio


def test_overlap_is_advisory_preserves_mixed_unknowns_and_survives_clear(tmp_path):
    store=Store(tmp_path)
    clip=dict(discovery_only=True,start=100,end=140,instance_id='receiver',synthetic=False,
              candidate_ids=['known','unidentified'],agencies=['Unknown tone activity'],allow_cloud=False,eligible=False)
    def detection(oid,start,end,**extra):
        event=dict(id=oid,at=start,end=end,instance_id='receiver',synthetic=False,agencies=['Fire'],tone_ids=['tone'],recording_id='normal-audio')
        event.update(extra);store.event('detection',event,start,oid)
    detection('overlap',101,109)
    detection('earlier',80,99)
    detection('later',140,145)
    detection('other',102,110,instance_id='another')
    detection('replay',102,110,synthetic=True)
    store.clear_history('events')
    result=context(store,clip)
    assert [x['id'] for x in result['known_page_overlaps']]==['overlap']
    assert result['candidate_ids']==['known','unidentified'] and not result['eligible'] and not result['allow_cloud']
    assert result['agencies']==clip['agencies'] and 'overlaps Fire' in label(result)
    assert 'Other tones' in result['discovery_note']
    assert 'known_page_overlaps' not in clip
    store.close();store=Store(tmp_path)
    assert len(context(store,clip)['known_page_overlaps'])==1
    store.close()


def test_late_detection_updates_existing_clip_without_renaming(tmp_path):
    store=Store(tmp_path)
    data=dict(discovery_only=True,start=100,end=120,instance_id='r',filename='Unknown_old.mp3')
    assert label(context(store,data))=='Discovery clip — unconfirmed'
    store.event('detection',dict(id='late',at=105,end=110,instance_id='r',agencies=['EMS']),105,'late')
    assert context(store,data)['filename']=='Unknown_old.mp3'
    assert 'overlaps EMS' in label(context(store,data))
    assert label(dict(agencies=['Known EMS']))=='Known EMS'
    store.close()


@pytest.mark.parametrize('replay,mode,allowed,expected',[(False,None,True,1),(True,None,True,0),(False,'ignore',True,0),(False,'record_only',True,0),(False,None,False,0)])
def test_notify_known_without_recording_and_suppression(tmp_path,monkeypatch,replay,mode,allowed,expected):
    c=defaults();c['playback']['notify_after_detection']=True;c['tones'][0]['record_enabled']=False
    e=Engine(tmp_path,c);calls=[]
    monkeypatch.setattr(e.alert_audio,'notify',lambda *a,**kw:calls.append(a))
    monkeypatch.setattr('tonepage.engine.test_mode',lambda *a:mode)
    e.replay_safe=replay;e.live_playback_allowed=lambda:allowed
    try:
        d=Detection(c['tones'][0]['id'],1,4,.9)
        e.detect(d,1000);e.detect(d,1000)
        assert len(calls)==expected and e.active is None and e.live_audio.session is None
    finally:e.close();e.store.close()


def test_discovery_alert_and_safe_replay(tmp_path,monkeypatch):
    c=defaults();c['playback']['discovery_alert']=True
    e=Engine(tmp_path,c);calls=[]
    monkeypatch.setattr(e.alert_audio,'notify',lambda *a,**kw:calls.append(a))
    candidate=dict(kind='long',a_hz=710,b_hz=None,a_seconds=3,b_seconds=None,start=0,end=3,quality=.9,gap_seconds=0)
    try:
        for replay in (False,True):
            e.replay_safe=replay;e.discovery.ready=[candidate.copy()];e.save_candidates(1000)
        assert len(calls)==1 and calls[0][2].startswith('discovery:')
        assert not e.store.recent('jobs')
    finally:e.close();e.store.close()


def test_alert_bounded_rate_limit_volume_and_cancellation(monkeypatch):
    audio=AlertAudio();blocks=[];entered=threading.Event();release=threading.Event()
    clock=[10.]
    monkeypatch.setattr('tonepage.alert_audio.time.monotonic',lambda:clock[0])
    def held(session):
        blocks.append(session['audio'].get(timeout=1)[1]);entered.set();release.wait(2)
    monkeypatch.setattr(audio,'_play',held)
    try:
        assert audio.notify(None,20,'discovery:a');assert entered.wait(1)
        assert not audio.notify(None,20,'discovery:b')
        assert np.max(np.abs(blocks[0]))<=.071 and len(blocks[0])==4800
        audio.stop();assert audio.session['cancel'].is_set()
        release.set();audio.stop(wait=True)
        clock[0]=13
        assert not audio.notify(None,20,'discovery:a')
        assert audio.notify(None,20,'discovery:b')
    finally:release.set();audio.close()


def test_alert_device_failure_does_not_escape_worker(monkeypatch):
    audio=AlertAudio()
    monkeypatch.setattr(audio,'_play',lambda session:(_ for _ in ()).throw(RuntimeError('missing device')))
    try:
        assert audio.notify(None)
        deadline=time.monotonic()+2
        while audio.session is not None and time.monotonic()<deadline:time.sleep(.01)
        assert audio.status.startswith('Alert audio error:') and audio.session is None
    finally:audio.close()


def test_alert_settings_validation():
    c=defaults();validate(c)
    c['playback']['alert_volume']=101
    with pytest.raises(ValueError):validate(c)
    c['playback']['alert_volume']=30;c['playback'].update(live_after_detection=True,notify_after_detection=True)
    with pytest.raises(ValueError,match='either'):validate(c)


def test_gui_mode_persists_and_legacy_live_selection(tmp_path,monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    from tonepage.config import load_config
    monkeypatch.setattr('tonepage.playback.output_devices', lambda sd: [])
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def children(w):
        for child in w.winfo_children():yield child;yield from children(child)
    def field(text):
        w=next(w for w in children(root) if isinstance(w,ttk.Label) and w.cget('text')==text)
        return w.master.grid_slaves(row=w.grid_info()['row'],column=1)[0]
    try:
        app.config['playback']['live_after_detection']=True
        app.playback_settings()
        mode=field('Known-tone listening mode');assert mode.get()=='Live dispatch audio'
        mode.set('Notify only')
        field('Alert volume (0-100)').delete(0,'end');field('Alert volume (0-100)').insert(0,'45')
        next(w for w in children(root) if isinstance(w,ttk.Button) and w.cget('text')=='Save playback device').invoke()
        playback=load_config(tmp_path)['playback']
        assert playback['notify_after_detection'] and not playback['live_after_detection'] and playback['alert_volume']==45
        assert app.engine.config['playback']==playback
    finally:app.close()
