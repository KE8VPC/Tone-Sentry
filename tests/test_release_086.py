import tkinter as tk
from tkinter import ttk
from tonepage.gui import Application


def walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from walk(child)


def test_diagnostics_and_sharing_review_are_read_only(tmp_path,monkeypatch):
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    errors=[];monkeypatch.setattr('tonepage.gui.messagebox.showerror',lambda *a,**k:errors.append(a))
    def click(label):
        next(w for w in walk(root) if isinstance(w,ttk.Button) and w.cget('text')==label).invoke()
        root.update()
    try:
        app.basic_settings();click('Audio diagnostics…');click('Copy audio diagnostics')
        assert 'selected_input' in root.clipboard_get()
        assert not app.engine.running
        app.config['tones'][0]['allow_cloud']=False
        app.config['integrations']=[dict(id='test',kind='ftp',enabled=True)]
        app.manage_integrations();click('Review tone sharing…')
        click(app.config['tones'][0]['agency'])
        assert not errors
        assert not app.config['tones'][0]['allow_cloud']
        assert 'Queued (local)' in app.jobs_tree['columns']
        assert 'Recording filename' in app.jobs_tree['columns']
    finally:
        app.engine.close();root.destroy()
