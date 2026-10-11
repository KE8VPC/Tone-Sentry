import threading
from tonepage.ftp_check import check_destination


def test_login_and_directory_readonly(tmp_path,monkeypatch):
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
    (tmp_path/'dispatch').mkdir()
    auth=DummyAuthorizer();auth.add_user('test','synthetic-password',str(tmp_path),perm='elr')
    class Handler(FTPHandler):pass
    Handler.authorizer=auth;Handler.auth_failed_timeout=0
    server=FTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=lambda:server.serve_forever(timeout=.1,blocking=True,handle_exit=False),daemon=True)
    thread.start()
    monkeypatch.setenv('FTP_CHECK_PASSWORD','synthetic-password')
    destination=dict(kind='ftp',host='127.0.0.1',port=server.socket.getsockname()[1],username='test',password_env='FTP_CHECK_PASSWORD',directory='/dispatch')
    try:
        ok,message=check_destination(destination)
        assert ok and 'Upload permission was not tested' in message
        from tonepage.ftp_credentials import encode_password
        stored=dict(destination,password_b64=encode_password('synthetic-password'),password_env='MISSING_LEGACY_VARIABLE')
        assert check_destination(stored)[0]
        ok,message=check_destination(dict(destination,directory='/missing'))
        assert not ok and 'directory access' in message
        monkeypatch.setenv('FTP_CHECK_PASSWORD','wrong-private-password')
        ok,message=check_destination(destination)
        assert not ok and 'login' in message and 'wrong-private-password' not in message
        assert list(tmp_path.iterdir())==[tmp_path/'dispatch']
        assert not list((tmp_path/'dispatch').iterdir())
    finally:server.close_all();thread.join(2)


def test_ftps_protection_and_cleanup(monkeypatch):
    calls=[]
    class Client:
        def __init__(self,context):assert context.check_hostname
        def __enter__(self):return self
        def __exit__(self,*args):calls.append('close')
        def connect(self,*args,**kwargs):calls.append('connect')
        def login(self,*args):calls.append('login')
        def prot_p(self):calls.append('protect')
        def cwd(self,path):calls.append(path)
        def pwd(self):calls.append('pwd');return '/dispatch'
    monkeypatch.setattr('tonepage.ftp_check.ftplib.FTP_TLS',Client)
    assert check_destination(dict(kind='ftps',host='example.invalid',directory='/dispatch'))[0]
    assert calls==['connect','login','protect','/dispatch','pwd','close']


def test_invalid_settings_and_missing_secret(monkeypatch):
    assert not check_destination(dict(kind='ftp',host='host',directory='../bad'))[0]
    monkeypatch.delenv('MISSING_FTP_CHECK_SECRET',raising=False)
    ok,message=check_destination(dict(kind='ftp',host='host',password_env='MISSING_FTP_CHECK_SECRET'))
    assert not ok and 'credentials' in message


def test_gui_uses_unsaved_values_without_saving(tmp_path,monkeypatch):
    import time
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    captured=[]
    def check(destination):captured.append(destination);return True,'Synthetic success'
    monkeypatch.setattr('tonepage.ftp_check.check_destination',check)
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def children(widget):
        for child in widget.winfo_children():yield child;yield from children(child)
    try:
        original=dict(id='test',kind='ftp',host='old.example',port=21,username='tester',directory='/dispatch',enabled=False)
        app.edit_integration(original,lambda:None)
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        label=next(w for w in children(win) if isinstance(w,ttk.Label) and w.cget('text')=='FTP host')
        entry=label.master.grid_slaves(row=label.grid_info()['row'],column=1)[0]
        entry.delete(0,'end');entry.insert(0,'new.example')
        password_label=next(w for w in children(win) if isinstance(w,ttk.Label) and w.cget('text')=='FTP password')
        password_entry=password_label.master.grid_slaves(row=password_label.grid_info()['row'],column=1)[0]
        assert password_entry.cget('show')
        password_entry.insert(0,'synthetic-form-password')
        button=next(w for w in children(win) if isinstance(w,ttk.Button) and w.cget('text')=='Test FTP connection')
        button.invoke()
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            root.update()
            if captured and str(button.cget('state'))=='normal':break
            time.sleep(.01)
        assert captured[0]['host']=='new.example'
        from tonepage.ftp_credentials import decode_password
        assert decode_password(captured[0]['password_b64'])=='synthetic-form-password'
        assert not app.config['integrations'] and original['host']=='old.example'
        assert str(button.cget('state'))=='normal'
        saved=[]
        app.config['integrations']=[original]
        monkeypatch.setattr(app,'apply',lambda config:saved.append(config))
        save_button=next(w for w in children(win) if isinstance(w,ttk.Button) and w.cget('text')=='Save destination')
        save_button.invoke()
        result=saved[0]['integrations'][0]
        assert decode_password(result['password_b64'])=='synthetic-form-password'
        import json
        assert 'synthetic-form-password' not in json.dumps(saved)
        assert 'password_env' not in result
    finally:app.close()
