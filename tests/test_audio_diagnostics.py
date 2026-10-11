import json
from types import SimpleNamespace
from tonepage.audio_diagnostics import input_inventory, input_choices, report, error_detail
from tonepage.sharing_feedback import blocked_agencies


def test_interfaces_preserve_identical_names_and_do_not_open_streams():
    sd=SimpleNamespace(query_hostapis=lambda:[{'name':'MME'},{'name':'Windows WASAPI'}],
        query_devices=lambda:[dict(name='USB',hostapi=i,max_input_channels=1,default_samplerate=48000) for i in (0,1)],
        default=SimpleNamespace(device=(1,2)),get_portaudio_version=lambda:(1,'test'))
    choices=input_choices(input_inventory(sd))
    assert choices['0: USB — MME']==0
    assert choices['1: USB — Windows WASAPI']==1
    data=json.loads(report(sd,1,0,16000))
    assert data['system_default_input']==1 and len(data['inputs'])==2
    assert data['inputs'][0]['default_sample_rate']==48000
    assert error_detail(ValueError('Invalid sample rate'),dict(device=1,channel=0,sample_rate=16000))['detail']=='Invalid sample rate'


def test_inventory_failure_is_reported():
    def fail():raise RuntimeError('Device enumeration failed')
    data=json.loads(report(SimpleNamespace(query_hostapis=fail),27,0,16000))
    assert data['inventory_error']=='Device enumeration failed'
    assert data['selected_input']==27


def test_sharing_feedback_filters_and_respects_permissions():
    config=dict(tones=[dict(id='a',agency='A',enabled=True,allow_cloud=False),dict(id='b',agency='B',enabled=True,allow_cloud=True)],
                integrations=[dict(kind='ftp',enabled=True,tone_ids=['a'])])
    assert [t['id'] for t in blocked_agencies(config)]==['a']
    config['integrations'][0]['tone_ids']=['b']
    assert not blocked_agencies(config)
    config['integrations']=[dict(kind='webhook',enabled=True)]
    assert not blocked_agencies(config)
    config['integrations'][0]['include_transcript']=True
    assert len(blocked_agencies(config))==1
