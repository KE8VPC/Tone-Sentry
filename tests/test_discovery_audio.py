import json
import wave
from pathlib import Path
import numpy as np
import pytest
from tonepage.config import defaults, validate
from tonepage.engine import Engine


def tone(hz, seconds):
    return .4*np.sin(2*np.pi*hz*np.arange(round(seconds*16000))/16000).astype('float32')


def feed(engine, *parts):
    data = np.concatenate(parts)
    for start in range(0, len(data), 640): engine.process(data[start:start+640])


def receiver(tmp_path, **settings):
    config = defaults()
    config['tones'] = []
    config['discovery'].update(enabled=True, record_enabled=True, **settings)
    validate(config)
    return Engine(tmp_path, config)


def test_original_first_tone_silence_stop_and_local_encode(tmp_path):
    e = receiver(tmp_path)
    try:
        e.config['coordination']['enabled'] = True
        e.client = object()  # Any call to the coordinator would fail.
        e.config['integrations'] = [dict(id='script', enabled=True, kind='script', triggers=['recording_complete'], scope='local', argv=['never-run'])]
        feed(e, np.zeros(16000), tone(710,1), tone(1110,3), np.zeros(16000*5))
        assert e.discovery_audio.active is None
        candidate = json.loads(e.candidates.rows()[0]['data'])
        row = e.store.recent('recordings')[0]
        assert candidate['recording_id'] == row['id'] == candidate['recent'][0]['recording_id']
        with wave.open(row['path']) as f:
            audio = np.frombuffer(f.readframes(f.getnframes()), '<i2')/32767
        assert np.allclose(audio[16000:32000], tone(710,1), atol=.0001)
        assert 7 <= len(audio)/16000 <= 8.5
        job = e.store.claim(['encode'])
        e.encode(job['payload']); e.store.finish(job)
        finished = e.store.recent('recordings')[0]
        assert finished['status'] == 'complete' and Path(finished['path']).stat().st_size > 500
        assert all(j['kind']=='encode' for j in e.store.recent('jobs'))
        with e.store.transaction() as db: db.execute('UPDATE recordings SET end=0')
        assert e.store.cleanup(1) == 1
        assert e.candidates.rows() and not Path(finished['path']).exists()
    finally:
        e.client = None
        e.close(); e.store.close()


def test_stack_shares_clip_repeat_observations_keep_separate_audio(tmp_path):
    e = receiver(tmp_path)
    try:
        for _ in range(2):
            feed(e, tone(710,1), tone(1110,3), tone(1310,1), tone(1510,3), np.zeros(16000*6))
        rows = e.candidates.rows()
        assert len(rows) == 3 and all(r['count']==2 for r in rows)
        groups = [json.loads(r['data']) for r in rows]
        assert all(g['ambiguous'] for g in groups)
        assert len({g['recent'][0]['recording_id'] for g in groups}) == 1
        assert len({g['recent'][1]['recording_id'] for g in groups}) == 1
        assert groups[0]['recent'][0]['recording_id'] != groups[0]['recent'][1]['recording_id']
        assert len(e.store.recent('recordings')) == 2
    finally: e.close(); e.store.close()


def test_maximum_stops_open_carrier_and_rearms_after_silence(tmp_path):
    e = receiver(tmp_path, audio_max_seconds=6.)
    try:
        feed(e, tone(710,20))
        rows = e.store.recent('recordings')
        assert len(rows) == 1 and e.discovery_audio.active is None
        data = json.loads(rows[0]['data'])
        assert data['maximum_duration_reached'] and data['samples'] == 6*16000
        feed(e, np.zeros(16000*5), tone(710,1), tone(1110,3), np.zeros(16000*5))
        assert len(e.store.recent('recordings')) == 2
    finally: e.close(); e.store.close()


def test_configured_recording_and_recovery_are_independent(tmp_path):
    config = defaults()
    config['discovery'].update(enabled=True, record_enabled=True)
    e = Engine(tmp_path, config)
    feed(e, tone(600,1), tone(900,3), np.zeros(16000*5))
    assert e.active is not None and e.discovery_audio.active is None
    rows = e.store.recent('recordings')
    assert len(rows) == 2
    assert {json.loads(r['data']).get('discovery_only',False) for r in rows} == {False,True}
    e.close(); e.store.close()
    recovered = Engine(tmp_path, config)
    try:
        jobs = recovered.store.recent('jobs')
        assert jobs and all(j['kind']=='encode' for j in jobs)
        assert any(json.loads(j['payload'])['data'].get('discovery_only') for j in jobs)
    finally: recovered.close(); recovered.store.close()


@pytest.mark.parametrize('settings', [dict(audio_silence_seconds=.3), dict(audio_max_seconds=5,audio_pre_roll=10), dict(record_enabled='yes')])
def test_invalid_capture_controls(settings):
    config = defaults(); config['discovery'].update(settings)
    with pytest.raises(ValueError): validate(config)
