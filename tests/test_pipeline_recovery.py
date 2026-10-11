import base64
import copy
import hashlib
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from tonepage.config import defaults
from tonepage.coordination import Coordinator
from tonepage.demo import signal
from tonepage.engine import Engine
from tonepage.integrations import JobWorker
from tonepage.store import Store


def process(e, data):
    for i in range(0, len(data), 640):
        e.process(data[i:i+640])


def test_weekly_test_in_mixed_stack_still_records_eligible_agency(tmp_path):
    c = defaults()
    c["tones"][0]["tests"] = [{"timezone": "UTC", "days": [0], "start": "00:00", "minutes": 60}]
    e = Engine(tmp_path, c)
    e.base_time = datetime(2026, 9, 7, 0, 10, tzinfo=timezone.utc).timestamp()
    process(e, np.concatenate([signal(600, 1), signal(900, 3), np.zeros(3200)]))
    assert e.active is None
    process(e, np.concatenate([signal(1000, 4), np.zeros(3200)]))
    assert e.active
    assert e.active["data"]["tone_ids"] == ["demo-all"]
    e.finish_recording()
    assert e.worker.run_one(("encode",))
    assert e.store.recent("recordings")[0]["status"] == "complete"
    e.close()


def test_recording_rollover_preserves_continuation(tmp_path):
    c = defaults()
    c["recording"].update(max_seconds=5, pre_roll=1, min_seconds=1, post_roll=.2, silence_seconds=.5)
    e = Engine(tmp_path, c)
    process(e, np.concatenate([signal(600, 1), signal(900, 3), signal(2000, 9), np.zeros(16000)]))
    e.finish_recording()
    while e.worker.run_one(("encode",)):
        pass
    rows = e.store.recent("recordings")
    assert len(rows) >= 2
    assert all(r["status"] == "complete" for r in rows)
    assert any(json.loads(r["data"]).get("continuation_of") for r in rows)
    assert len({r["path"] for r in rows}) == len(rows)
    e.close()


def test_encoding_recovery_from_interrupted_capture(tmp_path):
    c = defaults()
    e = Engine(tmp_path, c)
    process(e, np.concatenate([signal(600, 1), signal(900, 3), np.zeros(3200)]))
    assert e.active
    # Simulate process loss after its persisted recording checkpoint.
    e.active["writer"].close()
    e.active = None
    recovered = Engine(tmp_path, c, e.store)
    assert recovered.worker.run_one(("encode",))
    record = recovered.store.recent("recordings")[0]
    assert record["status"] == "complete"
    assert json.loads(record["data"])["interrupted"]
    recovered.close()
    e.close()


def test_script_timeout_marks_ambiguous_and_keeps_audio(tmp_path):
    s = Store(tmp_path)
    d = {"id": "hang", "kind": "script", "argv": [sys.executable, "-c", "import time; time.sleep(5)"], "timeout": .1}
    s.enqueue("script", "script", {"destination": d, "event": {"id": "e"}})
    worker = JobWorker(s, defaults())
    worker.run_one()
    assert s.recent("jobs")[0]["status"] == "ambiguous"
    assert not worker.run_one()


def test_duplicate_persistence_across_restart(tmp_path):
    c = defaults()
    e = Engine(tmp_path, c)
    raw = np.concatenate([signal(600, 1), signal(900, 3), np.zeros(3200)])
    process(e, raw)
    e.finish_recording()
    restarted = Engine(tmp_path, c, e.store)
    restarted.base_time = e.base_time+10
    process(restarted, raw)
    detections = [json.loads(r["data"]) for r in e.store.recent("events") if r["type"] == "detection"]
    assert detections[0]["duplicate"]
    restarted.finish_recording()
    e.close()
    restarted.close()


def test_coordinator_archive_isolation_preferred_recording_and_action_scope(tmp_path):
    c = defaults()
    c["coordinator"]["selection_wait_seconds"] = 5
    c["tones"][0]["allow_cloud"] = True
    c["integrations"] = [{"id": "transcribe", "kind": "transcription", "enabled": True, "url": "http://127.0.0.1:1"}]
    s = Store(tmp_path)
    coordinator = Coordinator(s, c)
    sid = None
    nodes = []
    for quality in (.4, .95):
        node = {"schema": 1, "instance_id": str(uuid.uuid4()), "boot_id": str(uuid.uuid4()), "site": "Site", "group": "default", "coverage": "channel"}
        nodes.append(node)
        coordinator.registration(node, True)
        obs = {"id": str(uuid.uuid4()), "type": "activation", "at": time.time()-3, "instance_id": node["instance_id"], "tone_ids": ["demo-fire"], "agencies": ["DEMO Fire"], "signature": ["two",600.,900.], "allow_cloud": True}
        current = coordinator.observation({**node, "event": obs})["shared_id"]
        assert sid is None or sid == current
        sid = current
        audio = b"ID3"+bytes([int(quality*100)])*100
        rec = {"recording_id": str(uuid.uuid4()), "instance_id": node["instance_id"], "detections": [obs], "sha256": hashlib.sha256(audio).hexdigest(), "start": obs["at"], "end": time.time(), "quality": quality, "allow_cloud": True}
        coordinator.recording({**node, "event": rec, "audio": base64.b64encode(audio).decode()})
    with s.transaction() as db:
        db.execute("UPDATE candidates SET received=received-6")
    coordinator.reconcile_actions()
    jobs = s.recent("jobs")
    assert len(jobs) == 1
    selected = json.loads(jobs[0]["payload"])
    assert selected["event"]["quality"] == .95
    assert selected["action_scope"] == "shared"
    recordings = s.recent("recordings")
    assert len(recordings) == 2 and len({r["path"] for r in recordings}) == 2
    assert all(Path(r["path"]).exists() for r in recordings)
    coordinator.c["revoked_instances"] = [nodes[0]["instance_id"]]
    with pytest.raises(PermissionError):
        coordinator.registration(nodes[0], True)
