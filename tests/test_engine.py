import json
import subprocess
import time
from pathlib import Path

import numpy as np

from tonepage.config import defaults
from tonepage.demo import signal, write_demo
from tonepage.engine import Engine, ffmpeg_exe


def feed(engine, data):
    for i in range(0, len(data), 640):
        engine.process(data[i:i+640])


def test_stacked_repeat_mp3_and_wave_decode(tmp_path):
    c = defaults()
    e = Engine(tmp_path, c)
    feed(e, np.concatenate([signal(600, 1), signal(900, 3), np.zeros(6400), signal(1000, 4), np.zeros(6400), signal(600, 1), signal(900, 3), np.zeros(1600)]))
    e.finish_recording()
    while e.worker.run_one():
        pass
    detections = [json.loads(r["data"]) for r in e.store.recent("events") if r["type"] == "detection"]
    assert len(detections) == 3
    assert sum(d["duplicate"] for d in detections) == 1
    records = e.store.recent("recordings")
    assert len(records) == 1
    assert records[0]["status"] == "complete"
    data = json.loads(records[0]["data"])
    assert data["agencies"] == ["DEMO All Call", "DEMO Fire"]
    result = subprocess.run([ffmpeg_exe(c), "-v", "error", "-i", records[0]["path"], "-f", "null", "-"], capture_output=True)
    assert result.returncode == 0, result.stderr
    assert Path(records[0]["path"]).with_suffix(".json").exists()
    e.close()


def test_replay_cannot_send_or_change_live_duplicate_state(tmp_path):
    c = defaults()
    c["integrations"] = [{"id": "hook", "kind": "webhook", "enabled": True, "url": "http://127.0.0.1:1", "triggers": ["activation", "recording_complete"]}]
    e = Engine(tmp_path, c)
    e.replay(write_demo(tmp_path / "input.wav", c))
    limit = time.monotonic()+10
    while e.store.rows("SELECT id FROM jobs WHERE status IN ('running','pending')") and time.monotonic() < limit:
        time.sleep(.05)
    assert all(j["kind"] == "encode" for j in e.store.recent("jobs"))
    assert e.store.get("activation:demo-fire") is None
    assert e.store.recent("recordings")[0]["status"] == "complete"
    e.close()

