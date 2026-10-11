import json
import smtplib
from email import policy
from email.parser import BytesParser
import pytest
from tonepage.config import defaults, validate
from tonepage.integrations import JobWorker, queue_actions
from tonepage.store import Store


def setup(tmp_path):
    c=defaults()
    c['integrations']=[dict(id='mail',kind='email',enabled=True,smtp_host='smtp.example.test',smtp_port=587,smtp_security='starttls',smtp_username='operator',smtp_password_env='TEST_SMTP_PASSWORD',email_from='dispatch@example.test',recipients=['one@example.test','two@example.test'])]
    validate(c)
    store=Store(tmp_path)
    path=tmp_path/'recordings'/'dispatch.mp3';path.parent.mkdir();path.write_bytes(b'ID3'+bytes(range(256)))
    event=dict(id='record:complete',recording_id='record',type='recording_complete',agencies=['Fire'],site='Test receiver',tone_ids=['demo-fire'],allow_cloud=True,path=str(path))
    return c,store,event,path


def test_mp3_email_mime_tls_and_separate_recipients(tmp_path,monkeypatch):
    c,store,event,path=setup(tmp_path);sent=[];steps=[]
    monkeypatch.setenv('TEST_SMTP_PASSWORD','test-only-secret')
    class SMTP:
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def ehlo(self): steps.append('ehlo')
        def starttls(self,context):
            assert context.check_hostname
            steps.append('tls')
        def login(self,user,password):
            assert 'tls' in steps and password=='test-only-secret'
            steps.append('login')
        def send_message(self,msg,from_addr,to_addrs):
            assert steps[-1]=='login'
            sent.append((BytesParser(policy=policy.default).parsebytes(msg.as_bytes()),to_addrs))
            return {}
    monkeypatch.setattr('tonepage.integrations.smtplib.SMTP',SMTP)
    queue_actions(store,c,event);queue_actions(store,c,event)
    worker=JobWorker(store,c)
    while worker.run_one(): pass
    assert len(sent)==2
    assert {tuple(x[1]) for x in sent}=={('one@example.test',),('two@example.test',)}
    for msg,recipients in sent:
        attachment=list(msg.iter_attachments())[0]
        assert attachment.get_content_type()=='audio/mpeg'
        assert attachment.get_payload(decode=True)==path.read_bytes()
        assert msg['To']==recipients[0]
        assert msg['Message-ID']
    assert all(j['status']=='done' for j in store.recent('jobs'))
    assert 'test-only-secret' not in json.dumps(store.recent('jobs'))


def test_email_sharing_tests_and_repeat_suppression(tmp_path):
    c,store,event,path=setup(tmp_path)
    for extra in [dict(allow_cloud=False),dict(test='ignore'),dict(duplicate=True)]:
        queue_actions(store,c,dict(event,**extra))
    assert not store.recent('jobs')


def test_email_attachment_limit_and_validation(tmp_path):
    c,store,event,path=setup(tmp_path)
    c['integrations'][0]['email_max_mb']=.00001
    queue_actions(store,c,event)
    worker=JobWorker(store,c)
    while worker.run_one(): pass
    assert all(j['status']=='failed' for j in store.recent('jobs'))
    c['integrations'][0]['email_max_mb']=15
    c['integrations'][0]['recipients']=['bad\r\nBcc: another@example.test']
    with pytest.raises(ValueError): validate(c)
