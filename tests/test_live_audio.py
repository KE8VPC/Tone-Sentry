import sys
import time
from types import SimpleNamespace
import numpy as np
import pytest
from tonepage.live_audio import LiveAudio, Resampler
from tonepage.config import defaults, validate
from tonepage.engine import Engine
from tonepage.detector import Detection


def until(predicate):
    deadline=time.monotonic()+3
    while not predicate() and time.monotonic()<deadline:time.sleep(.01)
    assert predicate()


@pytest.mark.parametrize('source,output',[(16000,48000),(44100,48000),(48000,44100)])
def test_resampler_continuity_across_blocks(source,output):
    data=np.linspace(-.5,.5,source,dtype=np.float32)
    converter=Resampler(source,output)
    pieces=[converter.feed(data[i:i+317]) for i in range(0,len(data),317)]
    actual=np.concatenate(pieces)
    positions=np.arange(0,len(data)-1,source/output)
    assert len(actual)==len(positions)
    np.testing.assert_allclose(actual,np.interp(positions,np.arange(len(data)),data),atol=1e-6)


def test_worker_selected_output_and_error_isolation(monkeypatch):
    writes=[];opened=[]
    class Stream:
        def __init__(self,**kwargs):opened.append(kwargs)
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def write(self,block):writes.append(block.copy())
        def abort(self):pass
    devices=[dict(name='Speakers',hostapi=0,max_output_channels=2,default_samplerate=48000)]
    sd=SimpleNamespace(query_hostapis=lambda:[dict(name='Test')],query_devices=lambda *args:devices[0] if args else devices,check_output_settings=lambda **kwargs:None,OutputStream=Stream)
    monkeypatch.setitem(sys.modules,'sounddevice',sd)
    audio=LiveAudio()
    try:
        audio.start(16000,dict(name='Speakers',hostapi='Test'))
        audio.feed(np.ones(640,dtype=np.float32)*.2)
        until(lambda:len(writes)>0)
        assert opened[0]['device']==0 and writes[0].shape[1]==2
        audio.finish();until(lambda:audio.session is None)
        audio.start(16000,dict(name='Missing',hostapi='Test'))
        until(lambda:audio.status.startswith('Live audio error:'))
        assert audio.session is None
    finally:audio.close()


def test_pending_output_queue_bounded_and_cancelled(monkeypatch):
    # Hold the worker before device opening while capture continues feeding.
    import threading
    entered=threading.Event();release=threading.Event()
    audio=LiveAudio()
    def held(session):entered.set();release.wait(3)
    monkeypatch.setattr(audio,'_play',held)
    try:
        audio.start(16000,None);assert entered.wait(1)
        for _ in range(200):audio.feed(np.zeros(640,dtype=np.float32))
        assert audio.session['audio'].qsize()==25
        audio.stop();assert audio.session['cancel'].is_set()
        release.set();until(lambda:audio.session is None)
    finally:release.set();audio.close()


@pytest.mark.parametrize('enabled,replay,mode,record,allowed,starts',[
    (True,False,None,True,True,1),(False,False,None,True,True,0),
    (True,True,None,True,True,0),(True,False,'ignore',True,True,0),
    (True,False,'record_only',True,True,0),(True,False,None,False,True,0),
    (True,False,None,True,False,0)])
def test_engine_arms_only_eligible_live_recording(tmp_path,monkeypatch,enabled,replay,mode,record,allowed,starts):
    config=defaults();config['playback']['live_after_detection']=enabled
    config['tones'][0]['record_enabled']=record
    e=Engine(tmp_path,config);calls=[]
    monkeypatch.setattr('tonepage.engine.test_mode',lambda *args:mode)
    monkeypatch.setattr(e.live_audio,'start',lambda rate,device:calls.append((rate,device)))
    e.live_playback_allowed=lambda:allowed;e.replay_safe=replay
    try:
        d=Detection(config['tones'][0]['id'],1,4,.9)
        e.detect(d,1000);e.detect(d,1000)
        assert len(calls)==starts  # repeated/stacked notifications do not reopen output
    finally:e.close();e.store.close()


def test_duplicate_does_not_start_new_live_session(tmp_path,monkeypatch):
    config=defaults();config['playback']['live_after_detection']=True
    e=Engine(tmp_path,config);calls=[]
    monkeypatch.setattr(e.live_audio,'start',lambda *args:calls.append(args))
    try:
        e.store.set('activation:'+config['tones'][0]['id'],1000)
        e.detect(Detection(config['tones'][0]['id'],1,4,.9),1000)
        assert not calls
        assert e.active is not None
    finally:e.close();e.store.close()


def test_live_option_validates_and_defaults_off():
    config=defaults();assert not config['playback']['live_after_detection']
    config['playback']['live_after_detection']='yes'
    with pytest.raises(ValueError):validate(config)


def test_live_audio_follows_recording_and_continues_across_parts(tmp_path,monkeypatch):
    config=defaults();config['playback']['live_after_detection']=True
    config['recording'].update(pre_roll=0,min_seconds=0,max_seconds=1,silence_seconds=100)
    e=Engine(tmp_path,config);calls=[]
    for name in ('start','feed','finish'):
        monkeypatch.setattr(e.live_audio,name,lambda *args,n=name:calls.append(n))
    try:
        e.detect(Detection(config['tones'][0]['id'],0,.04,.9),1000)
        first=e.active['data']['recording_id']
        for i in range(30):e.process(np.zeros(640,dtype=np.float32),1000+i*.04)
        assert e.active['data']['recording_id']!=first
        assert e.active['live_started']
        assert calls.count('start')==1 and calls.count('feed')==30
        assert calls.count('finish')==0
        e.finish_recording();assert calls.count('finish')==1
    finally:e.close();e.store.close()
