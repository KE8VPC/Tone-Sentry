import hashlib
import json
from datetime import datetime, timezone
from importlib.resources import files

import numpy as np
import pytest

from tonepage.config import defaults, validate, test_mode as mode_at
from tonepage.importer import import_other_application
from tonepage.reference import catalog, entries, frequency_for_code
from tonepage.engine import Engine
from tonepage.demo import signal


def test_reference_complete_and_undefined_codes_rejected():
    assert len(entries()) == 256
    assert len(entries(selectable_only=True)) == 236
    assert entries(query='Plectron')
    assert frequency_for_code(0) > 100
    for code in [30,31,62,63,240,255]:
        with pytest.raises(ValueError): frequency_for_code(code)
    assert files('tonepage').joinpath('resources/tone-chart.pdf').read_bytes().startswith(b'%PDF')
    assert hashlib.sha256(files('tonepage').joinpath('resources/tone-chart.pdf').read_bytes()).hexdigest()==catalog()['source_sha256']
    assert 'SCHEDULER' in files('tonepage').joinpath('resources/usage-guide.md').read_text()


def test_fd_import_preserves_supported_settings_and_warns(tmp_path):
    source={'audio':{'sampleRate':44100},'recording':{'autoDeleteOlderThanDays':7},'detection':{'minRecordingLengthSec':30,'maxRecordingLengthSec':45,'detectors':[
        {'name':'Fire','tones':[911,3000],'tolerancePercent':.02,'lockoutTimeoutMs':6000,'minRecordingLengthSec':45,'maxRecordingLengthSec':60,'notifications':{'password':'PRIVATE'}},
        {'name':'All call','tones':[1000],'isRecordingEnabled':False},
        {'name':'Six tones','tones':[602,926,602,636,636,602]}]}}
    path=tmp_path/'source.json'; path.write_text(json.dumps(source))
    c,notes=import_other_application(path,defaults()); validate(c)
    assert len(c['tones'])==2
    assert all(not t['enabled'] for t in c['tones'])
    assert c['tones'][0]['tolerance_percent']==.02
    assert c['tones'][0]['duplicate_seconds']==6
    assert c['tones'][0]['record_max_seconds']==60
    assert not c['tones'][1]['record_enabled']
    assert c['recording']['retention_days']==7
    assert 'PRIVATE' not in json.dumps(c)
    assert any('SKIPPED Six tones' in n for n in notes)
    assert c['tones'][0]['id']==import_other_application(path,defaults())[0]['tones'][0]['id']
    assert json.loads(path.read_text())==source


def test_disabled_weekly_schedule_and_midnight():
    c=defaults(); tone=c['tones'][0]
    tone['tests']=[dict(days=[0],start='23:58',minutes=5,timezone='UTC',mode='ignore',enabled=True)]
    stamp=datetime(2026,9,8,0,1,tzinfo=timezone.utc).timestamp()
    validate(c); assert mode_at(tone,stamp)=='ignore'
    tone['tests'][0]['enabled']=False
    assert mode_at(tone,stamp) is None


def test_record_disabled_and_duration_override(tmp_path):
    for enabled in (False,True):
        c=defaults(); t=c['tones'][0]
        t.update(record_enabled=enabled,record_min_seconds=20,record_max_seconds=40)
        engine=Engine(tmp_path/str(enabled),c)
        try:
            data=np.concatenate([signal(600,1),signal(900,3),np.zeros(1600)])
            for i in range(0,len(data),640): engine.process(data[i:i+640])
            assert bool(engine.active)==enabled
            assert engine.store.recent('events')
            if enabled:
                assert engine.active['data']['record_min_seconds']==20
                assert engine.active['data']['record_max_seconds']==40
        finally: engine.close()


def test_percentage_tolerance_changes_actual_detection(tmp_path):
    for percent in (None,.05):
        c=defaults(); c['tones']=[c['tones'][1]]
        if percent: c['tones'][0]['tolerance_percent']=percent
        engine=Engine(tmp_path/str(percent),c)
        try:
            data=np.concatenate([signal(1030,4),np.zeros(1600)])
            for i in range(0,len(data),640): engine.process(data[i:i+640])
            assert bool(engine.store.recent('events'))==bool(percent)
        finally: engine.close()
