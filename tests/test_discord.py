import json
from tonepage.config import defaults
from tonepage.integrations import webhook_payload, is_discord_webhook, queue_actions, JobWorker
from tonepage.store import Store

URL='https://discord.com/api/webhooks/123/example-token'


def test_discord_message_format_and_size():
    event={'id':'event','type':'transcript_complete','site':'Site','agencies':['Fire @everyone'],'text':'🚒'*3000,'path':'private'}
    payload=webhook_payload({'url':URL,'include_transcript':True},event)
    assert 0<len(payload['content'].encode('utf-16-le'))//2<=2000
    assert payload['allowed_mentions']=={'parse':[]}
    assert 'private' not in json.dumps(payload)
    assert 'Transcript:' not in webhook_payload({'url':URL},event)['content']
    assert webhook_payload({'url':URL,'webhook_format':'generic'},event)==event
    assert not is_discord_webhook('https://discord.com.attacker.test/api/webhooks/123/token')
    assert not is_discord_webhook('https://discord.com/api/channels/123')


def test_existing_queued_discord_destination_uses_fixed_payload(tmp_path,monkeypatch):
    captured=[]
    monkeypatch.setattr('tonepage.integrations.post',lambda url,**kw:captured.append(json.loads(kw['data'])))
    c=defaults(); c['integrations']=[dict(id='discord',kind='webhook',enabled=True,url=URL,triggers=['activation'])]
    store=Store(tmp_path)
    event=dict(id='alert1',type='activation',agencies=['Fire'],site='Receiver',tone_ids=['demo-fire'],path='private',text='private transcript')
    queue_actions(store,c,event)
    assert JobWorker(store,c).run_one()
    assert captured[0]['content'].startswith('Fire - ')
    assert 'Receiver:' not in captured[0]['content']
    assert 'Event:' not in captured[0]['content']
    assert 'Recording:' not in captured[0]['content']
    assert 'private' not in json.dumps(captured)
    assert store.recent('jobs')[0]['status']=='done'


def test_discord_compact_format_uses_event_time():
    from datetime import datetime
    stamp=datetime(2026,9,7,14,5).timestamp()
    event=dict(at=stamp,agencies=['Wapak FD/EMS'],site='laptopx',id='private-event',recording_id='private-recording')
    assert webhook_payload({'url':URL},event)['content']=='Wapak FD/EMS - 2:05 PM'


def test_custom_template_and_validation():
    import pytest
    from datetime import datetime
    from tonepage.config import validate_discord_template
    event=dict(at=datetime(2026,9,7,14,5).timestamp(),agencies=['Fire','EMS'],site='laptop',id='evt',recording_id='rec',text='Dispatch text')
    d=dict(url=URL,discord_template='{date} | {agency} | {time}\n{site}\n{transcript}',include_transcript=True)
    assert webhook_payload(d,event)['content']=='2026-09-07 | Fire, EMS | 2:05 PM\nlaptop\nDispatch text'
    d['include_transcript']=False
    assert 'Dispatch text' not in webhook_payload(d,event)['content']
    for bad in ['','{agency.__class__}','{unknown}','{agency!r}','{time:>999999}','unclosed {']:
        with pytest.raises(ValueError): validate_discord_template(bad)
