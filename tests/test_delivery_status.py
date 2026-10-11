import pytest
from tonepage.store import Store
from tonepage.delivery_status import display_status,related_upload


def queued(store):
    store.enqueue('action:event:upload','ftp',dict(destination=dict(id='upload',password_b64='PRIVATE-VALUE'),event={}))
    store.enqueue('notice','webhook',dict(destination=dict(id='notice',wait_for_ftp='upload',url='https://private.invalid/token'),event=dict(id='event',type='recording_complete',filename='Page_abc123.mp3')))
    return store.rows("SELECT * FROM jobs WHERE id='notice'")[0]


@pytest.mark.parametrize('state,label',[('pending','Waiting for FTP'),('running','Waiting for FTP'),('failed','Upload failed'),('cancelled','Upload cancelled'),('done','Ready to send')])
def test_status_tracks_upload_without_mutating_queue(tmp_path,state,label):
    store=Store(tmp_path);row=queued(store)
    with store.transaction() as db:db.execute("UPDATE jobs SET status=? WHERE kind='ftp'",(state,))
    assert display_status(store,row)==label
    assert store.rows("SELECT status FROM jobs WHERE id='notice'")[0]['status']=='pending'


def test_ready_to_retry_and_terminal_notification(tmp_path):
    store=Store(tmp_path);queued(store)
    with store.transaction() as db:
        db.execute("UPDATE jobs SET status='done' WHERE kind='ftp'")
        db.execute("UPDATE jobs SET status='failed',error='Required FTP upload failed or was cancelled' WHERE id='notice'")
    row=dict(store.rows("SELECT * FROM jobs WHERE id='notice'")[0])
    assert display_status(store,row)=='Ready to retry'
    row.update(status='done');assert display_status(store,row)=='Completed'
    row.update(status='cancelled');assert display_status(store,row)=='Cancelled'
    with store.transaction() as db:db.execute("DELETE FROM jobs WHERE kind='ftp'")
    row.update(status='pending');assert display_status(store,row)=='Upload not queued'


def test_details_can_open_hidden_upload_without_secrets(tmp_path):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def children(widget):
        for child in widget.winfo_children():yield child;yield from children(child)
    try:
        app.engine.worker.stop();queued(app.engine.store)
        app.engine.store.clear_history('jobs',mode='all')
        app.delivery_detail('notice')
        texts=[str(w.cget('text')) for w in children(root) if isinstance(w,ttk.Label)]
        assert any('Waiting for FTP' in t for t in texts)
        button=next(w for w in children(root) if isinstance(w,ttk.Button) and w.cget('text')=='Open related upload')
        button.invoke()
        texts=[str(w.cget('text')) for w in children(root) if isinstance(w,ttk.Label)]
        assert any('Destination: upload' in t for t in texts)
        assert all('PRIVATE-VALUE' not in t and 'private.invalid' not in t for t in texts)
        assert not app.engine.store.visible_history('jobs')
    finally:app.close()
