import copy
import json
import threading
import time
import numpy as np
import pytest
from tonepage.config import defaults
from tonepage.engine import Engine
from tonepage.integrations import queue_actions


def test_delivery_changes_keep_existing_jobs_and_engine(tmp_path):
    c=defaults();c['integrations']=[dict(id='notify',kind='script',enabled=True,scope='local',argv=['old'])]
    e=Engine(tmp_path,c)
    try:
        e.running=True
        event=dict(id='first',type='recording_complete',tone_ids=[],allow_cloud=True)
        queue_actions(e.store,e.delivery_config,event)
        new=copy.deepcopy(c);new['integrations'][0]['argv']=['new']
        detector=e.detector
        e.request_settings(new,lambda c:None)
        queue_actions(e.store,e.delivery_config,dict(event,id='second'))
        rows=e.store.rows('SELECT payload FROM jobs ORDER BY created')
        assert [json.loads(r['payload'])['destination']['argv'] for r in rows]==[['old'],['new']]
        assert e.detector is detector and e.running and e.pending_settings is None
    finally:e.running=False;e.close();e.store.close()


def test_tone_change_waits_for_sequence_and_recording(tmp_path):
    e=Engine(tmp_path,defaults());e.running=True
    try:
        new=copy.deepcopy(e.config);new['tones'][0]['a_hz']=650
        e.detector.states['demo-fire']['stage']='gap'
        old=e.detector
        e.request_settings(new,lambda c:None)
        with e.settings_lock:e._apply_pending_settings()
        assert e.detector is old
        e.detector.states['demo-fire']['stage']=None
        e.begin_recording(time.time())
        snapshot=dict(e.active['data']['encoding_settings'])
        with e.settings_lock:e._apply_pending_settings()
        assert e.detector is old and e.active
        e.finish_recording()
        with e.settings_lock:e._apply_pending_settings()
        assert e.detector is not old and e.config['tones'][0]['a_hz']==650
        assert json.loads(e.store.rows("SELECT payload FROM jobs WHERE kind='encode'")[0]['payload'])['data']['encoding_settings']==snapshot
    finally:e.running=False;e.close();e.store.close()


def test_failed_save_and_latest_pending_update(tmp_path):
    e=Engine(tmp_path,defaults());e.running=True
    try:
        new=copy.deepcopy(e.config);new['input']['sample_rate']=48000
        def fail(c):raise OSError('disk full')
        with pytest.raises(OSError):e.request_settings(new,fail)
        assert e.pending_settings is None and e.rate==16000
        e.request_settings(new,lambda c:None)
        e.request_settings(copy.deepcopy(e.config),lambda c:None)
        assert e.pending_settings is None and not e.audio_reconfigure.is_set()
    finally:e.running=False;e.close();e.store.close()


def test_replay_failure_finishes_recording_before_applying_pending(tmp_path,monkeypatch):
    from tonepage.demo import write_demo
    e=Engine(tmp_path,defaults())
    monkeypatch.setattr(e,'start_workers',lambda:None)
    path=write_demo(tmp_path/'demo.wav',e.config)
    def fail(samples,stamp=None):
        e.begin_recording(time.time())
        new=copy.deepcopy(e.config);new['input']['sample_rate']=48000
        e.request_settings(new,lambda c:None)
        raise RuntimeError('Replay read failed')
    monkeypatch.setattr(e,'process',fail)
    try:
        with pytest.raises(RuntimeError):e.replay(path)
        assert e.active is None and e.rate==48000 and e.pending_settings is None
        payload=json.loads(e.store.rows("SELECT payload FROM jobs WHERE kind='encode'")[0]['payload'])
        assert payload['data']['interrupted']
    finally:e.close();e.store.close()


def test_capture_reopens_after_queue_drains_without_stopping_monitoring(tmp_path,monkeypatch):
    import sounddevice as sd
    opened=[]
    class Stream:
        active=True
        def __init__(self,**kw):self.kw=kw
        def __enter__(self):opened.append(self.kw['samplerate']);return self
        def __exit__(self,*args):pass
    monkeypatch.setattr(sd,'InputStream',Stream)
    e=Engine(tmp_path,defaults());e.running=True
    e.capture_thread=threading.Thread(target=e._capture_loop)
    e.processing_thread=threading.Thread(target=e._process_loop)
    e.capture_thread.start();e.processing_thread.start()
    try:
        deadline=time.monotonic()+3
        while not opened and time.monotonic()<deadline:time.sleep(.01)
        new=copy.deepcopy(e.config);new['input']['sample_rate']=48000
        e.request_settings(new,lambda c:None)
        while len(opened)<2 and time.monotonic()<deadline:time.sleep(.02)
        assert opened==[16000,48000]
        assert e.running and e.rate==48000 and e.pending_settings is None
    finally:e.close();e.store.close()


def test_audio_swap_waits_for_captured_blocks(tmp_path):
    e=Engine(tmp_path,defaults());e.running=True
    try:
        new=copy.deepcopy(e.config);new['input']['sample_rate']=48000
        e.request_settings(new,lambda c:None)
        e.audio_paused.set();e.audio_queue.put((np.zeros(640),time.time(),False))
        with e.settings_lock:e._apply_pending_settings()
        assert e.rate==16000
        e.audio_queue.get_nowait()
        with e.settings_lock:e._apply_pending_settings()
        assert e.rate==48000
    finally:e.running=False;e.close();e.store.close()


def test_failed_source_can_switch_without_waiting_for_missing_tone_end(tmp_path,monkeypatch):
    import sounddevice as sd
    opened=[]
    class Stream:
        active=True
        def __init__(self,**kw):self.rate=kw['samplerate']
        def __enter__(self):
            if self.rate==16000:raise RuntimeError('Input disconnected')
            opened.append(self.rate);return self
        def __exit__(self,*args):pass
    monkeypatch.setattr(sd,'InputStream',Stream)
    e=Engine(tmp_path,defaults());e.running=True
    e.detector.states['demo-fire']['stage']='gap'
    e.begin_recording(time.time())
    e.capture_thread=threading.Thread(target=e._capture_loop)
    e.processing_thread=threading.Thread(target=e._process_loop)
    e.capture_thread.start();e.processing_thread.start()
    try:
        assert e.audio_failed.wait(2)
        new=copy.deepcopy(e.config);new['input']['sample_rate']=48000
        e.request_settings(new,lambda c:None)
        deadline=time.monotonic()+6
        while not opened and time.monotonic()<deadline:time.sleep(.02)
        assert opened==[48000] and e.running
        payload=json.loads(e.store.rows("SELECT payload FROM jobs WHERE kind='encode'")[0]['payload'])
        assert payload['data']['interrupted'] is True
    finally:e.close();e.store.close()
