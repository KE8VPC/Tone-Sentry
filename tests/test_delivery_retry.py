import json
import pytest
from tonepage.config import defaults
from tonepage.store import Store
from tonepage.delivery_retry import refreshed_payload,retry_with_settings


def setup_job():
    config=defaults()
    old=dict(id='ftp',kind='ftp',enabled=True,scope='local',host='old',password_env='OLD')
    config['integrations']=[dict(old,host='new',password_b64='bmV3')]
    payload=dict(destination=old,event=dict(type='recording_complete',allow_cloud=True,recording_id='record',path='audio/test.mp3'),action_scope='local')
    return config,dict(id='job',kind='ftp',status='failed',payload=payload)


def test_retry_updates_settings_without_changing_event_or_job_id(tmp_path):
    config,job=setup_job();store=Store(tmp_path)
    store.enqueue(job['id'],job['kind'],job['payload'])
    with store.transaction() as db:db.execute("UPDATE jobs SET status='failed',attempts=8,error='old failure'")
    retry_with_settings(store,'job',config)
    result=store.rows('SELECT * FROM jobs')[0]
    payload=json.loads(result['payload'])
    assert payload['destination']['host']=='new'
    assert payload['event']==job['payload']['event']
    assert result['id']=='job' and result['status']=='pending' and result['attempts']==0 and result['error'] is None
    claimed=store.claim()
    with pytest.raises(ValueError):retry_with_settings(store,'job',config)
    store.finish(claimed)
    with pytest.raises(ValueError):retry_with_settings(store,'job',config)


@pytest.mark.parametrize('change',[dict(enabled=False),dict(kind='ftps'),dict(scope='shared'),dict(tone_ids=['different'])])
def test_retry_rejects_incompatible_destination(change):
    config,job=setup_job();config['integrations'][0].update(change)
    with pytest.raises(ValueError):refreshed_payload(job,config)


def test_email_retry_keeps_original_recipient():
    config,job=setup_job();job['kind']='email'
    job['payload']['destination'].update(kind='email',recipients=['a@example.invalid'])
    config['integrations'][0].update(kind='email',recipients=['a@example.invalid','b@example.invalid'])
    assert refreshed_payload(job,config)['destination']['recipients']==['a@example.invalid']
    config['integrations'][0]['recipients']=['b@example.invalid']
    with pytest.raises(ValueError):refreshed_payload(job,config)


def test_removed_destination_and_sharing_denial():
    config,job=setup_job();job['payload']['event']['allow_cloud']=False
    with pytest.raises(ValueError):refreshed_payload(job,config)
    config['integrations']=[]
    with pytest.raises(ValueError):refreshed_payload(job,config)


def test_gui_retry_cancel_and_confirm(tmp_path,monkeypatch):
    import tkinter as tk
    from tonepage.gui import Application
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        app.engine.worker.stop()
        config,job=setup_job();app.config['integrations']=config['integrations']
        app.engine.store.enqueue('job','ftp',job['payload'])
        with app.engine.store.transaction() as db:db.execute("UPDATE jobs SET status='failed' WHERE id='job'")
        app.jobs_tree.insert('', 'end',iid='job',values=('ftp','ftp','failed',8,'failure'))
        app.jobs_tree.selection_set('job')
        monkeypatch.setattr('tonepage.gui.messagebox.askyesno',lambda *_,**__:False)
        app.retry_saved_settings()
        assert app.engine.store.rows("SELECT status FROM jobs WHERE id='job'")[0]['status']=='failed'
        monkeypatch.setattr('tonepage.gui.messagebox.askyesno',lambda *_,**__:True)
        app.retry_saved_settings()
        row=app.engine.store.rows("SELECT * FROM jobs WHERE id='job'")[0]
        assert row['status']=='pending' and json.loads(row['payload'])['destination']['host']=='new'
    finally:app.close()
