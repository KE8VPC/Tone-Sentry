import copy
import json
import socket
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from tonepage.config import defaults, save_config
from tonepage.engine import Engine
from tonepage.receiver_controller import ReceiverController, revision
from tonepage.web_console import create_app, DEFAULTS, set_account, WebConsole, save_access, load_access


@pytest.fixture
def receiver(tmp_path):
    config=defaults()
    engine=Engine(tmp_path,config)
    owner=SimpleNamespace(engine=engine,config=config)
    def apply(c):
        engine.request_settings(c,lambda value:save_config(tmp_path,value))
        owner.config=copy.deepcopy(c)
    owner.apply=apply
    controller=ReceiverController(owner)
    settings=copy.deepcopy(DEFAULTS)
    set_account(settings,'admin','testing-password-123','admin')
    set_account(settings,'reader','testing-password-456','viewer')
    app=create_app(controller,engine.store,settings)
    client=app.test_client()
    yield owner,controller,settings,app,client
    controller.close()
    engine.close()


BASE='https://localhost:8767'
def call(client,path,method='GET',**kwargs):
    headers={'Origin':BASE,**kwargs.pop('headers',{})}
    return client.open(path,method=method,base_url=BASE,headers=headers,**kwargs)


def login(client,name='admin',password='testing-password-123'):
    response=call(client,'/api/session','POST',json=dict(username=name,password=password))
    assert response.status_code==200
    cookie=response.headers['Set-Cookie']
    assert all(flag in cookie for flag in ('Secure','HttpOnly','SameSite=Strict'))
    return call(client,'/api/session').json['csrf']


def test_auth_csrf_origin_host_and_logout(receiver):
    o,c,s,app,client=receiver
    for path in ('/api/status','/api/recordings','/api/recordings/no/audio','/api/activity','/api/tones'):
        assert call(client,path).status_code==401
    csrf=login(client)
    assert call(client,'/api/status').status_code==200
    assert call(client,'/api/status',headers={'Host':'evil.test:8767'}).status_code==400
    assert client.get('/api/status',base_url='http://localhost:8767').status_code==400
    assert call(client,'/api/commands/pause','POST',json={}).status_code==403
    assert call(client,'/api/commands/pause','POST',json={},headers={'X-CSRF-Token':csrf,'Origin':'https://evil.test'}).status_code==403
    assert call(client,'/api/session','DELETE',headers={'X-CSRF-Token':csrf}).status_code==200
    assert call(client,'/api/status').status_code==401


def test_signin_creates_one_overview_event_without_credentials(receiver):
    o,c,s,app,client=receiver
    assert call(client,'/api/session','POST',json={'username':'admin','password':'wrong'}).status_code==401
    assert not o.engine.store.rows("SELECT * FROM events WHERE type='web_sign_in'")
    login(client)
    for _ in range(3):
        assert call(client,'/api/status').status_code==200
        assert call(client,'/api/recordings').status_code==200
    rows=o.engine.store.rows("SELECT * FROM events WHERE type='web_sign_in'")
    assert len(rows)==1
    d=json.loads(rows[0]['data'])
    assert d['actor']=='admin' and d['client_ip']=='127.0.0.1'
    assert 'Web console accessed: admin from 127.0.0.1' in d['message']
    assert 'testing-password' not in rows[0]['data'] and 'csrf' not in rows[0]['data']


def test_viewer_cannot_mutate_and_expired_session(receiver):
    o,c,s,app,client=receiver
    csrf=login(client,'reader','testing-password-456')
    assert call(client,'/api/commands/stop','POST',json={},headers={'X-CSRF-Token':csrf}).status_code==403
    access=app.extensions['tone_access']
    for session in access.sessions.values():session['seen']-=1801
    assert call(client,'/api/status').status_code==401


def test_throttle_and_size_limit(receiver):
    client=receiver[-1]
    for i in range(10):
        assert call(client,'/api/session','POST',json=dict(username='missing',password='wrong')).status_code==401
    assert call(client,'/api/session','POST',json=dict(username='missing',password='wrong')).status_code==429
    assert call(client,'/api/session','POST',json={'data':'x'*40000}).status_code==413


def test_commands_revision_validation_idempotency_and_desktop_busy(receiver):
    o,c,s,app,client=receiver
    csrf=login(client)
    headers={'X-CSRF-Token':csrf,'Idempotency-Key':'unique-key-1'}
    result=call(client,'/api/commands/pause','POST',headers=headers,json={})
    assert result.status_code==202 and not o.engine.detection_paused
    oid=result.json['id']
    assert call(client,'/api/commands/pause','POST',headers=headers,json={}).json['id']==oid
    assert call(client,'/api/commands/resume','POST',headers=headers,json={}).status_code==409
    c.pump()
    assert o.engine.detection_paused
    assert call(client,'/api/operations/'+oid).json['status']=='applied'
    original=copy.deepcopy(o.config)
    data=dict(id='demo-fire',revision=revision(o.config),tone={'agency':'New agency','enabled':False})
    oid=c.submit('save-tone',data,'admin','edit1')
    c.pump()
    assert c.operation(oid,'admin')['status']=='applied'
    assert o.config['tones'][0]['agency']=='New agency'
    assert o.engine.config['tones'][0]['agency']=='New agency'
    stale=c.submit('save-tone',data,'admin','edit2');c.pump()
    assert c.operation(stale,'admin')['status']=='failed'
    invalid=c.submit('save-tone',dict(data,revision=revision(o.config),tone={'a_hz':-1}),'admin','edit3');c.pump()
    assert c.operation(invalid,'admin')['status']=='failed'
    assert o.config['tones'][0]['a_hz']==original['tones'][0]['a_hz']
    c.busy=lambda:True
    busy=c.submit('resume',{},'admin','resume1');c.pump()
    assert c.operation(busy,'admin')['status']=='failed'
    assert o.engine.detection_paused
    assert c.operation(oid,'reader') is None


def test_recordings_ranges_redaction_deleted_and_path_boundary(receiver,tmp_path):
    o,c,s,app,client=receiver
    audio=tmp_path/'audio';audio.mkdir()
    path=audio/'hello.mp3';path.write_bytes(b'0123456789'*100)
    data=dict(agencies=['Test agency'],path='secret path',encoding_settings={'secret':'password'},detections=[{'secret':'token'}])
    o.engine.store.recording('one',100,110,'complete',path,data)
    login(client)
    listing=call(client,'/api/recordings').json
    assert listing['items'][0]['filename']=='hello.mp3'
    assert 'secret' not in json.dumps(listing)
    response=call(client,'/api/recordings/one/audio',headers={'Range':'bytes=10-19'})
    assert response.status_code==206 and response.data==b'0123456789'
    assert response.headers['Content-Range']=='bytes 10-19/1000'
    assert response.headers['Cache-Control']=='no-store'
    response.close()
    assert call(client,'/api/recordings/one/audio',headers={'Range':'bytes=9999-'}).status_code==416
    outside=tmp_path/'outside.mp3';outside.write_bytes(b'no')
    o.engine.store.recording('outside',100,110,'complete',outside,{})
    assert call(client,'/api/recordings/outside/audio').status_code==404
    o.engine.store.recording('active',100,110,'capturing',path,{})
    assert call(client,'/api/recordings/active/audio').status_code==404
    path.unlink()
    assert call(client,'/api/recordings/one/audio').status_code==404
    oid=c.submit('clear-deleted',{},'admin','clear1');c.pump()
    assert c.operation(oid,'admin')['status']=='applied'
    assert not any(r['id']=='one' for r in call(client,'/api/recordings').json['items'])


def test_pause_discards_partial_tones_and_keeps_existing_recording(receiver):
    o,c,*_=receiver
    e=o.engine
    e.config['discovery']['enabled']=True
    e.discovery.settings['enabled']=True
    e.begin_recording(100)
    rid=e.active['data']['recording_id']
    e.detector.states['demo-fire']['stage']='a'
    e.discovery.current={'start':0,'end':1}
    e.pause_detection(True)
    assert e.discovery.current is None and e.detector.states['demo-fire']['stage'] is None
    def must_not_feed(*args):raise AssertionError('Paused detector fed samples')
    original=e.detector.feed;e.detector.feed=must_not_feed
    e.process(np.ones(640,dtype=np.float32)*.02,100)
    assert e.active['data']['recording_id']==rid
    assert e.active['data']['samples']>=640
    e.detector.feed=original
    e.pause_detection(False)
    assert not e.detection_paused and all(v['stage'] is None for v in e.detector.states.values())
    e.finish_recording(interrupted=True)


def test_deferred_tone_edit_and_failed_persistence(receiver,monkeypatch):
    o,c,*_=receiver
    e=o.engine
    e.running=True
    e.begin_recording(100)
    data=dict(id='demo-fire',revision=revision(o.config),tone={'agency':'Deferred'})
    oid=c.submit('save-tone',data,'admin','deferred');c.pump()
    assert c.operation(oid,'admin')['result']['pending_settings']
    assert e.config['tones'][0]['agency']=='DEMO Fire'
    assert e.pending_settings['tones'][0]['agency']=='Deferred'
    e.running=False;e.finish_recording(interrupted=True)
    with e.settings_lock:e._apply_pending_settings()
    assert e.config['tones'][0]['agency']=='Deferred'
    def failure(config):raise OSError('disk failure')
    o.apply=failure
    oid=c.submit('save-tone',dict(data,revision=revision(o.config),tone={'agency':'Failed'}),'admin','failure');c.pump()
    assert c.operation(oid,'admin')['status']=='failed'
    assert o.config['tones'][0]['agency']=='Deferred'


def test_real_https_listener_and_account_storage(receiver,tmp_path):
    import requests
    o,c,s,*_=receiver
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    s.update(port=port,enabled=True)
    save_access(tmp_path,s)
    assert load_access(tmp_path)['enabled']
    assert 'testing-password' not in (tmp_path/'web-access.json').read_text()
    w=WebConsole(tmp_path,c,o.engine.store)
    try:
        w.start(s)
        url=f'https://localhost:{port}'
        cert=str(tmp_path/'web-tls/certificate.pem')
        response=requests.get(url,verify=cert,timeout=5)
        assert response.status_code==200 and 'TONE SENTRY' in response.text
        session=requests.Session()
        response=session.post(url+'/api/session',headers={'Origin':url},json=dict(username='admin',password='testing-password-123'),verify=cert,timeout=5)
        assert response.status_code==200
        assert session.get(url+'/api/status',verify=cert,timeout=5).status_code==200
    finally:w.stop()


def test_pause_maximum_does_not_start_another_part(receiver):
    e=receiver[0].engine
    e.begin_recording(100)
    e.active['data']['record_max_seconds']=.02
    e.pause_detection(True)
    e.process(np.ones(640,dtype=np.float32)*.02,100)
    assert e.active is None
    assert len(e.store.recent('recordings'))==1


def test_disable_revokes_pending_commands_and_preserves_tone_schedules(receiver):
    o,c,*_=receiver
    oid=c.submit('pause',{},'admin','pause-pending')
    c.cancel_pending();c.pump()
    assert not o.engine.detection_paused
    assert c.operation(oid,'admin')['status']=='failed'
    o.config['tones'][0]['tests']=[dict(enabled=False,timezone='UTC',days=[0],start='12:00',minutes=5,mode='ignore')]
    oid=c.submit('save-tone',dict(id='demo-fire',revision=revision(o.config),tone={'agency':'Keep schedule'}),'admin','keep-schedule')
    c.pump()
    assert c.operation(oid,'admin')['status']=='applied'
    assert o.config['tones'][0]['tests'][0]['start']=='12:00'


def test_windowed_listener_survives_rejected_tls_and_plain_http(receiver,tmp_path,monkeypatch):
    import ssl
    import sys
    import time
    import requests
    o,c,s,*_=receiver
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    s.update(enabled=True,port=port)
    w=WebConsole(tmp_path,c,o.engine.store)
    try:
        w.start(s)
        with monkeypatch.context() as patch:
            patch.setattr(sys,'stderr',None)
            patch.setattr(sys,'stdout',None)
            # An untrusted certificate rejected by a client, as on a first browser visit.
            with socket.create_connection(('127.0.0.1',port),timeout=3) as raw:
                with pytest.raises(ssl.SSLCertVerificationError):
                    ssl.create_default_context().wrap_socket(raw,server_hostname='localhost')
            # Also tolerate accidentally speaking plain HTTP to the HTTPS port.
            with socket.create_connection(('127.0.0.1',port),timeout=3) as raw:
                raw.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n')
                try:raw.recv(1024)
                except OSError:pass
            time.sleep(.2)
            result=requests.get(f'https://localhost:{port}/',verify=str(tmp_path/'web-tls/certificate.pem'),timeout=5)
            assert result.status_code==200
            assert w.thread.is_alive()
        assert o.engine.store.rows("SELECT id FROM events WHERE type='web_connection_warning'")
        # Even a full/unavailable diagnostic store must not break connection handling.
        w._last_warning=0
        def fail(*args,**kwargs):raise OSError('test store unavailable')
        monkeypatch.setattr(o.engine.store,'event',fail)
        w.server_error('not recorded: request secrets')
    finally:w.stop()
