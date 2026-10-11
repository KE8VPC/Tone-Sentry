import json
import pytest
from tonepage.config import defaults, validate
from tonepage.integrations import webhook_payload, is_google_chat_webhook, PermanentError, JobWorker, queue_actions
from tonepage.store import Store

URL = 'https://chat.googleapis.com/v1/spaces/ABC_123/messages?key=fake&token=fake'

def test_auto_detection_and_payload():
    assert is_google_chat_webhook(URL)
    for bad in (URL.replace('https:', 'http:'), URL.replace('googleapis.com', 'googleapis.com.evil'), URL.split('?')[0], 'https://['):
        assert not is_google_chat_webhook(bad)
    event=dict(type='recording_complete',agencies=['Fire EMS'],filename='Fire_EMS #1.mp3',text='Private transcript',path='C:/private/Fire_EMS #1.mp3')
    d=dict(url=URL,google_chat_template='{agency}\nhttps://example.org/audio/{filename_url}\n{transcript}')
    p=webhook_payload(d,event)
    assert set(p)=={'text'} and 'Fire_EMS%20%231.mp3' in p['text']
    assert 'Private' not in p['text'] and 'C:/' not in p['text']
    d['include_transcript']=True
    assert 'Private transcript' in webhook_payload(d,event)['text']
    d['google_chat_template']='{agency}'
    assert webhook_payload(d,event)['text'].endswith('Transcript: Private transcript')

def test_validation_and_limits():
    c=defaults();d=dict(id='chat',kind='webhook',enabled=True,url=URL,webhook_format='google_chat')
    c['integrations']=[d];validate(c)
    d['url']='https://example.org'
    with pytest.raises(ValueError,match='complete HTTPS'):validate(c)
    d['url']=URL;d['google_chat_template']='{bad}'
    with pytest.raises(ValueError,match='placeholder'):validate(c)
    with pytest.raises(PermanentError,match='empty'):
        webhook_payload(dict(webhook_format='google_chat',google_chat_template='{filename}'),dict(type='activation'))
    with pytest.raises(PermanentError,match='too large'):
        webhook_payload(dict(webhook_format='google_chat',include_transcript=True),dict(text='x'*40000))

def test_queued_google_delivery_and_suppression(tmp_path,monkeypatch):
    import tonepage.integrations as integration
    sent=[]
    monkeypatch.setattr(integration,'post',lambda url,**kw:sent.append((url,json.loads(kw['data']))))
    c=defaults();c['integrations']=[dict(id='chat',kind='webhook',enabled=True,url=URL,webhook_format='google_chat',include_transcript=True,triggers=['transcript_complete'])]
    store=Store(tmp_path)
    event=dict(id='event',type='transcript_complete',agencies=['EMS'],text='Dispatch text',allow_cloud=True)
    queue_actions(store,c,event);queue_actions(store,c,event)
    worker=JobWorker(store,c);assert worker.run_one();assert not worker.run_one()
    assert sent==[(URL,{'text':webhook_payload(c['integrations'][0],event)['text']})]
    for extra in (dict(duplicate=True),dict(allow_cloud=False),dict(test="ignore")):
        queue_actions(store,c,dict(event,id=str(extra),**extra))
    assert not worker.run_one()
