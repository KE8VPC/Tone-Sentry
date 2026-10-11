import tkinter as tk
from tkinter import ttk
from tonepage.gui import Application


def descendants(widget):
    for child in widget.winfo_children():yield child;yield from descendants(child)


def test_type_and_auto_url_visibility_and_hidden_validation(tmp_path,monkeypatch):
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        app.edit_integration(None,lambda:None)
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        def label(text):return next(w for w in descendants(win) if isinstance(w,ttk.Label) and w.cget('text')==text)
        def field(text):
            w=label(text);return w.master.grid_slaves(row=w.grid_info()['row'],column=1)[0]
        kind=field('Destination type');url=field('Webhook / transcription URL')
        preview=next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Preview Discord message')
        assert not preview.winfo_manager()
        url.insert(0,'https://discord.com/api/webhooks/123/test-token')
        assert preview.winfo_manager()=='grid'
        url.delete(0,'end');url.insert(0,'https://[')
        assert not preview.winfo_manager()
        url.delete(0,'end');url.insert(0,'https://discord.com/api/webhooks/123/test-token')
        assert not label('Generic webhook message template (optional)').winfo_manager()
        url.delete(0,'end');url.insert(0,'https://chat.googleapis.com/v1/spaces/ABC/messages?key=fake&token=fake')
        assert label('Google Chat message template').winfo_manager()=='grid'
        assert not preview.winfo_manager()
        assert not label('API token environment variable').winfo_manager()
        chat_preview=next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Preview Google Chat message')
        assert chat_preview.winfo_manager()=='grid'
        kind.set('ftp')
        assert not preview.winfo_manager()
        assert label('FTP password').winfo_manager()=='grid'
        assert not label('Email recipients (one plain email address per item)').winfo_manager()
        kind.set('email')
        assert label('Email recipients (one plain email address per item)').winfo_manager()=='grid'
        assert not label('FTP password').winfo_manager()
        kind.set('transcription')
        assert label('Transcription provider form fields').winfo_manager()=='grid'
        assert not label('Email recipients (one plain email address per item)').winfo_manager()
        kind.set('ftps')
        assert label('FTP password').winfo_manager()=='grid'
        assert not label('Trigger: tone detected').winfo_manager()
        kind.set('ftp')
        field('FTP port').set('invalid-hidden-number')
        kind.set('script')
        assert label('Script file').winfo_manager()=='grid'
        assert not label('FTP password').winfo_manager()
        script=field('Script file');script.insert(0,str(tmp_path/'script.bat'))
        saved=[];monkeypatch.setattr(app,'apply',lambda c:saved.append(c))
        button=next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Save destination')
        button.invoke()
        assert saved[0]['integrations'][0]['script_file']==str(tmp_path/'script.bat')
        assert 'port' not in saved[0]['integrations'][0]
    finally:app.close()


def test_legacy_script_untouched_when_file_not_chosen(tmp_path,monkeypatch):
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        original=dict(id='legacy',kind='script',argv=['cmd.exe','/d','/c','C:/receipt.bat','{filename}'])
        app.config['integrations']=[original]
        app.edit_integration(original,lambda:None)
        saved=[];monkeypatch.setattr(app,'apply',lambda c:saved.append(c))
        button=next(w for w in descendants(root) if isinstance(w,ttk.Button) and w.cget('text')=='Save destination')
        button.invoke()
        assert saved[0]['integrations'][0]['argv']==original['argv']
        assert 'script_file' not in saved[0]['integrations'][0]
    finally:app.close()
