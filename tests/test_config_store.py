import copy
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tonepage.config import defaults, validate, test_mode as schedule_mode, safe_name
from tonepage.importer import import_twotonedetect
from tonepage.store import InstanceLock, Store


def test_schedule_midnight_and_dst_fold():
    tone = {"tests": [{"timezone": "America/New_York", "days": [0], "start": "23:58", "minutes": 5, "mode": "ignore"}]}
    assert schedule_mode(tone, datetime(2026, 9, 8, 4, 1, tzinfo=timezone.utc).timestamp()) == "ignore"
    assert schedule_mode(tone, datetime(2026, 9, 8, 4, 4, tzinfo=timezone.utc).timestamp()) is None
    tone["tests"][0].update(days=[6], start="01:30", minutes=15)
    for hour in (5, 6):
        assert schedule_mode(tone, datetime(2026, 11, 1, hour, 35, tzinfo=timezone.utc).timestamp()) == "ignore"


def test_import_allowlist_and_close_tolerance(tmp_path):
    source = tmp_path / "tones.cfg"
    source.write_text("[Tone1]\natone=349\nbtone=365\natonelength=.5\nbtonelength=1\ndescription=Fire\nignore_after=30\nmp3_emails=private@example.test\nalert_command=bad-command\n[Longtone1]\nlongtone=1000\nlongtonelength=5\ndescription=EMS\n")
    c, notes = import_twotonedetect(source, defaults())
    validate(c)
    assert c["tones"][0]["tolerance_hz"] == 6.4
    assert c["tones"][0]["duplicate_seconds"] == 30
    assert c["tones"][1]["kind"] == "long"
    assert "private@example" not in json.dumps(c)+str(notes)
    assert "bad-command" not in json.dumps(c)+str(notes)
    assert "private@example" in source.read_text()


def test_validation_rejects_filename_field_access():
    c = defaults()
    c["recording"]["filename"] = "{site.__class__}"
    with pytest.raises(ValueError):
        validate(c)
    assert "/" not in safe_name("../../foo:bar")
    assert safe_name("CON") == "_CON"


def test_lock_releases_after_close(tmp_path):
    lock = InstanceLock(tmp_path)
    with pytest.raises(RuntimeError):
        InstanceLock(tmp_path)
    lock.close()
    InstanceLock(tmp_path).close()


def test_queue_uniqueness_and_stale_claim(tmp_path):
    s = Store(tmp_path)
    s.enqueue("one", "webhook", {"x": 1})
    s.enqueue("one", "webhook", {"x": 2})
    j = s.claim()
    assert j["payload"] == {"x": 1}
    assert s.claim() is None
    s.recover()
    newer = s.claim()
    s.finish(j)
    assert s.recent("jobs")[0]["status"] == "running"
    s.finish(newer)
    assert s.recent("jobs")[0]["status"] == "done"
    s.close()


def test_retention_ownership_and_pending_work(tmp_path):
    s = Store(tmp_path)
    root = tmp_path / "recordings"
    root.mkdir()
    old = time.time()-86400*10
    owned = root / "old.mp3"
    protected = root / "pending.mp3"
    outside = tmp_path / "unrelated.mp3"
    for p in (owned, protected, outside):
        p.write_bytes(b"audio")
        s.recording(p.stem, old, old+10, "complete", p, {})
    s.enqueue("waiting", "ftp", {"recording_id": "pending"})
    assert s.cleanup(1) == 1
    assert not owned.exists() and protected.exists() and outside.exists()
    s.close()

