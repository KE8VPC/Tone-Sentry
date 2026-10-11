import json
import tkinter as tk
import numpy as np
import pytest
from tonepage.config import defaults,validate
from tonepage.detector import Detector
from tonepage.discovery import Discovery,draft
from tonepage.discovery_review import selected_candidate
from tonepage.demo import signal
from tonepage.gui import Application


def capture(parts,**settings):
    c=defaults();c['discovery'].update(enabled=True,**settings)
    detector=Detector(c);observer=Discovery(c['discovery'],detector.dt);detector.observer=observer
    audio=np.concatenate(parts)
    for i in range(0,len(audio),640):detector.feed(audio[i:i+640])
    observer.finish()
    return observer.drain()


def test_stack_selects_disjoint_pairs_and_preserves_gaps():
    data=capture([signal(600,1),signal(900,3),np.zeros(3200),signal(1200,1),signal(1500,3),np.zeros(16000)])[0]
    first=selected_candidate(data,[0,1]);second=selected_candidate(data,[2,3])
    assert (first['a_hz'],first['b_hz'])==pytest.approx((600,900),abs=2)
    assert (second['a_hz'],second['b_hz'])==pytest.approx((1200,1500),abs=2)
    assert data['sequence'][2]['gap_before']==pytest.approx(.2,abs=.08)
    c=defaults();c['tones']=[draft(first),draft(second)];validate(c)
    assert all(not t['enabled'] and not t['allow_cloud'] for t in c['tones'])
    with pytest.raises(ValueError):selected_candidate(data,[0,2])
    with pytest.raises(ValueError):selected_candidate(data,[])
    assert selected_candidate(data,[1])['kind']=='long'


def test_dropout_bridge_is_bounded_and_does_not_merge_different_tones():
    parts=[signal(700,.32),np.zeros(640),signal(700,.32),signal(1100,3),np.zeros(16000)]
    assert capture(parts,dropout_seconds=.08)[0]['a_seconds']==pytest.approx(.68,abs=.08)
    assert not any(r['kind']=='two' for r in capture(parts,dropout_seconds=0))
    parts=[signal(700,.32),np.zeros(6400),signal(700,.32),signal(1100,3),np.zeros(16000)]
    assert not any(r['kind']=='two' for r in capture(parts,dropout_seconds=.08))


def test_discovery_purity_does_not_lower_configured_detection_threshold(monkeypatch):
    c=defaults();c['detector']['min_purity']=.95;c['discovery'].update(enabled=True,min_purity=.7)
    detector=Detector(c);observer=Discovery(c['discovery'],detector.dt);detector.observer=observer
    results=[]
    for frequency,seconds in [(600,1),(900,3),(None,1)]:
        monkeypatch.setattr(detector,'frequency',lambda frame,minimum_purity=None,f=frequency:(f,.8 if f else 0))
        results+=detector.feed(np.zeros(int(seconds*16000)))
    assert not results
    assert len(observer.drain())==1


def test_close_pair_and_low_frequency_between_pages():
    data=capture([signal(638,1),signal(653,3),signal(136.5,2.5),signal(1615,9),np.zeros(16000)],min_hz=250,stability_hz=12)
    assert [r['kind'] for r in data]==['two','long']
    assert data[0]['a_hz']==pytest.approx(638,abs=2)
    assert data[0]['b_hz']==pytest.approx(653,abs=2)
    assert data[1]['a_seconds']==pytest.approx(9,abs=.08)


def test_review_dialog_does_not_enable_or_alter_library(tmp_path):
    root=tk.Tk();root.withdraw();app=Application(root,tmp_path)
    try:
        data=capture([signal(600,1),signal(900,3),signal(1200,1),signal(1500,3),np.zeros(16000)])[0]
        cid=app.engine.candidates.observe(data,'live',1000)
        app.unknown_only.set(False);app.refresh_discovery();app.candidate_tree.selection_set(cid)
        before=json.dumps(app.config['tones'],sort_keys=True)
        app.review_sequence();root.update()
        assert any(w.title()=='Review captured sequence / split stacked pages' for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        assert json.dumps(app.config['tones'],sort_keys=True)==before
    finally:app.engine.close();root.destroy()
