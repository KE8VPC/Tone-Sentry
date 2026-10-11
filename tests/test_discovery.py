import json
import numpy as np
import pytest
from tonepage.config import defaults,validate
from tonepage.detector import Detector
from tonepage.discovery import Discovery,Candidates,configured_matches,draft
from tonepage.engine import Engine
from tonepage.demo import signal
from tonepage.store import Store


def discover(parts, settings=None, finish=True):
    c=defaults(); c['tones']=[]
    c['discovery'].update(enabled=True,**(settings or {}))
    detector=Detector(c);observer=Discovery(c['discovery'],detector.dt);detector.observer=observer
    samples=np.concatenate(parts)
    for start in range(0,len(samples),317): detector.feed(samples[start:start+317])
    if finish: observer.finish()
    return observer.drain()


def test_unknown_pair_and_longtone_without_library():
    rows=discover([signal(712.5,1),signal(1122.5,3),np.zeros(16000),signal(1555,4),np.zeros(16000)])
    assert [r['kind'] for r in rows]==['two','long']
    assert rows[0]['a_hz']==pytest.approx(712.5,abs=2)
    assert rows[0]['b_hz']==pytest.approx(1122.5,abs=2)
    assert rows[0]['a_seconds']==pytest.approx(1,abs=.08)
    assert rows[0]['b_seconds']==pytest.approx(3,abs=.08)
    assert not rows[0]['ambiguous']
    c=defaults();c['tones']=[draft(r) for r in rows];validate(c)
    assert all(not t['enabled'] and not t['allow_cloud'] for t in c['tones'])


@pytest.mark.parametrize('parts',[
    [signal(700,.2),signal(1100,.2),np.zeros(16000)],
    [signal(700,16),np.zeros(16000)],
    [signal(700,1,amplitude=.001),signal(1100,3,amplitude=.001)],
    [signal(700,1)+signal(1300,1),signal(1100,3)+signal(1900,3)],
    [np.random.default_rng(8).normal(0,.15,16000*6)],
])
def test_reject_non_candidates(parts):
    assert discover(parts)==[]


def test_stack_flags_overlapping_pairs_and_clock_reset():
    rows=discover([signal(600,1),signal(900,3),signal(1200,1),signal(1500,3),np.zeros(16000)])
    assert len(rows)==3 and all(r['ambiguous'] for r in rows)
    assert [round(r['a_hz']) for r in rows]==[600,900,1200]
    c=defaults();c['discovery']['enabled']=True
    detector=Detector(c);observer=Discovery(c['discovery'],detector.dt);detector.observer=observer
    detector.feed(signal(600,1));detector.reset()
    detector.feed(np.concatenate([signal(900,1),np.zeros(16000)]))
    observer.finish();assert observer.drain()==[]


def test_persistence_repeat_groups_and_source_separation(tmp_path):
    row=discover([signal(700,1),signal(1100,3),np.zeros(16000)])[0]
    store=Store(tmp_path);candidates=Candidates(store)
    candidates.observe(row,'live',1000)
    candidates.observe(row,'live',1100)
    candidates.observe(row,'replay',1200)
    assert sorted(x['count'] for x in candidates.rows())==[1,2]
    store.close();store=Store(tmp_path)
    assert len(Candidates(store).rows())==2
    store.close()


def test_discovery_never_queues_notifications_or_records_unknown(tmp_path):
    c=defaults();c['tones']=[];c['discovery']['enabled']=True
    c['integrations']=[dict(id='hook',enabled=True,kind='webhook',triggers=['activation'],url='https://example.invalid')]
    e=Engine(tmp_path,c)
    samples=np.concatenate([signal(700,1),signal(1100,3),np.zeros(16000)])
    for start in range(0,len(samples),640):e.process(samples[start:start+640])
    assert len(e.candidates.rows())==1
    assert not e.store.recent('jobs') and not e.store.recent('recordings')
    e.close()


def test_matching_library_and_truncated_end():
    row=discover([signal(600,1),signal(900,3)])[0]
    assert row['truncated']
    assert configured_matches(row,defaults()['tones'])==['DEMO Fire']
