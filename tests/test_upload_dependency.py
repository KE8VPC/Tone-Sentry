import pytest
from tonepage.config import defaults,validate
from tonepage.integrations import JobWorker,queue_actions
from tonepage.store import Store


def setup(tmp_path):
    config=defaults()
    config['integrations']=[dict(id='notice',kind='webhook',enabled=True,scope='local',wait_for_ftp='upload'),
                            dict(id='upload',kind='ftp',enabled=True,scope='local')]
    event=dict(id='page:complete',type='recording_complete',recording_id='page',allow_cloud=True,path='audio/Page.mp3')
    store=Store(tmp_path);queue_actions(store,config,event,'local')
    return config,store


def test_waits_without_spending_retries_and_survives_worker_restart(tmp_path):
    config,store=setup(tmp_path);sent=[]
    worker=JobWorker(store,config,handlers={'webhook':lambda p:sent.append(p),'ftp':lambda p:None})
    for _ in range(12):
        with store.transaction() as db:db.execute("UPDATE jobs SET due=0 WHERE kind='webhook'")
        assert worker.run_one(('webhook',))
    row=store.rows("SELECT * FROM jobs WHERE kind='webhook'")[0]
    assert not sent and row['status']=='pending' and row['attempts']==0 and 'Waiting' in row['error']
    worker=JobWorker(store,config,handlers=worker.handlers)
    assert worker.run_one(('ftp',))
    with store.transaction() as db:db.execute("UPDATE jobs SET due=0 WHERE kind='webhook'")
    assert worker.run_one(('webhook',)) and len(sent)==1
    assert not worker.run_one(('webhook',))


@pytest.mark.parametrize('state',['failed','cancelled','missing'])
def test_missing_or_unsuccessful_upload_never_posts(tmp_path,state):
    config,store=setup(tmp_path);sent=[]
    with store.transaction() as db:
        if state=='missing':db.execute("DELETE FROM jobs WHERE kind='ftp'")
        else:db.execute("UPDATE jobs SET status=? WHERE kind='ftp'",(state,))
    worker=JobWorker(store,config,handlers={'webhook':lambda p:sent.append(p)})
    worker.run_one(('webhook',))
    assert not sent and store.rows("SELECT status FROM jobs WHERE kind='webhook'")[0]['status']=='failed'


def test_configuration_requires_matching_scope_and_complete_event():
    c=defaults()
    c['integrations']=[dict(id='ftp',kind='ftp',scope='local'),dict(id='web',kind='webhook',scope='local',wait_for_ftp='ftp')]
    validate(c)
    c['integrations'][1]['scope']='shared'
    with pytest.raises(ValueError,match='scope'):validate(c)
    c['integrations'][1].update(scope='local',triggers=['activation'])
    with pytest.raises(ValueError,match='Recording complete'):validate(c)


def test_unselected_dependency_keeps_normal_behavior(tmp_path):
    config,store=setup(tmp_path)
    import json
    row=store.rows("SELECT * FROM jobs WHERE kind='webhook'")[0]
    payload=json.loads(row['payload']);payload['destination'].pop('wait_for_ftp')
    with store.transaction() as db:db.execute('UPDATE jobs SET payload=? WHERE id=?',(json.dumps(payload),row['id']))
    sent=[];worker=JobWorker(store,config,handlers={'webhook':lambda p:sent.append(p)})
    worker.run_one(('webhook',))
    assert len(sent)==1


def test_gui_upload_selector_saves_stable_destination_id(tmp_path,monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    def children(widget):
        for child in widget.winfo_children():yield child;yield from children(child)
    try:
        app.config['integrations']=[dict(id='upload',name='Website audio',kind='ftp',enabled=False)]
        saved=[];monkeypatch.setattr(app,'apply',lambda c:saved.append(c))
        app.edit_integration(None,lambda:None)
        label=next(w for w in children(root) if isinstance(w,ttk.Label) and w.cget('text')=='Wait for successful FTP upload')
        select=label.master.grid_slaves(row=label.grid_info()['row'],column=1)[0]
        assert select.get()=='Do not wait'
        select.set('Website audio (upload)')
        button=next(w for w in children(root) if isinstance(w,ttk.Button) and w.cget('text')=='Save destination')
        button.invoke()
        assert saved[0]['integrations'][-1]['wait_for_ftp']=='upload'
        validate(saved[0])
    finally:app.close()
