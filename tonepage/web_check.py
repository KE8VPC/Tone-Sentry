"""Isolated packaged HTTPS integration check; no live input or external delivery."""
import copy
import socket
import time


def check(app, recording):
    import requests
    from .web_console import DEFAULTS, set_account
    s=copy.deepcopy(DEFAULTS)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        s.update(enabled=True,port=sock.getsockname()[1])
    set_account(s,'package-test','isolated-test-password','admin')
    web=app.web_console
    # Clear test-only dialogs; they correctly block remote mutations.
    import tkinter as tk
    for child in app.root.winfo_children():
        if isinstance(child,tk.Toplevel):child.destroy()
    app.receiver_controller.publish()
    web.start(s)
    url=f"https://localhost:{s['port']}"
    session=requests.Session()
    cert=str(app.home/'web-tls/certificate.pem')
    def request(method,path,**kw):
        return session.request(method,url+path,verify=cert,timeout=8,**kw)
    try:
        import ssl
        # First browser visits commonly reject the generated certificate. This
        # must not kill logging/the listener in a windowed executable without stderr.
        with socket.create_connection(('127.0.0.1',s['port']),timeout=5) as raw:
            try:
                ssl.create_default_context().wrap_socket(raw,server_hostname='localhost')
            except ssl.SSLCertVerificationError:
                pass
            else:
                raise AssertionError('Isolated generated certificate was unexpectedly trusted')
        assert request('GET','/api/status').status_code==401
        assert request('GET','/').status_code==200
        assert request('GET','/console.js').status_code==200
        assert request('GET','/console.css').status_code==200
        r=request('POST','/api/session',headers={'Origin':url},json={'username':'package-test','password':'isolated-test-password'})
        assert r.status_code==200,r.text
        csrf=request('GET','/api/session').json()['csrf']
        status=request('GET','/api/status').json()
        assert status['version']
        result=request('GET','/api/recordings').json()
        assert result['items']
        r=request('GET','/api/recordings/'+recording['id']+'/audio',headers={'Range':'bytes=0-99'})
        assert r.status_code==206 and len(r.content)==100
        headers={'Origin':url,'X-CSRF-Token':csrf,'Idempotency-Key':'package-pause-check'}
        r=request('POST','/api/commands/pause',headers=headers,json={})
        assert r.status_code==202,r.text
        app.receiver_controller.pump()
        assert app.engine.detection_paused
        assert request('GET','/api/operations/'+r.json()['id']).json()['status']=='applied'
        headers['Idempotency-Key']='package-tone-check'
        tone_id=app.config['tones'][0]['id']
        rev=request('GET','/api/tones').json()['revision']
        r=request('POST','/api/commands/save-tone',headers=headers,json={'id':tone_id,'revision':rev,'tone':{'agency':'Package web edit'}})
        assert r.status_code==202
        app.receiver_controller.pump()
        assert request('GET','/api/operations/'+r.json()['id']).json()['status']=='applied'
        assert app.config['tones'][0]['agency']=='Package web edit'
        app.engine.pause_detection(False)
        assert request('DELETE','/api/session',headers=headers).status_code==200
        assert request('GET','/api/status').status_code==401
        signins=app.engine.store.rows("SELECT data FROM events WHERE type='web_sign_in'")
        assert len(signins)==1 and 'package-test' in signins[0]['data']
        web.stop()
        web.start(s)
        assert request('GET','/api/status').status_code==401
        assert request('GET','/').status_code==200
        from .network_reference import local_addresses
        assert isinstance(local_addresses(),str)
        return 'HTTPS survives rejected certificate; login audit, logout, assets, MP3 Range, pause, tone edit, listener restart and local address enumeration passed'
    finally:
        session.close()
        web.stop()
