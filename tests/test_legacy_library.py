"""Sanitized frequency/timing fixtures from the supplied legacy file; no recipients."""
import numpy as np
import pytest
from tonepage.config import defaults, validate
from tonepage.demo import signal
from tonepage.detector import Detector
from tonepage.importer import import_twotonedetect


PAIRS = [(419,618,.5), (768,1699,.5), (408,328,.5), (935,650,.5),
         (1516,596,.5), (634,650,.5), (2145,596,.5), (2145,1697,.5),
         (586,812,.5), (2247,596,.5), (338,376,.5), (1699,596,.5),
         (349,365,.5), (419,338,.5), (328,408,1), (877.4,517.5,1)]
LONGS = [1516,1613,2048,1000]


def library(tmp_path):
    lines = []
    for i, (a,b,duration) in enumerate(PAIRS, 1):
        lines += [f"[Tone{i}]", f"atone={a}", f"btone={b}", "atonelength=.5", f"btonelength={duration}", f"description=Agency {i}"]
    for i, hz in enumerate(LONGS, 1):
        lines += [f"[Longtone{i}]", f"longtone={hz}", "longtonelength=5", f"description=Long agency {i}"]
    path = tmp_path / "tones.cfg"
    path.write_text("\n".join(lines))
    c, _ = import_twotonedetect(path, defaults())
    return validate(c)


@pytest.mark.parametrize("index", range(20))
def test_all_imported_sets_do_not_cross_trigger(tmp_path, index):
    c = library(tmp_path)
    tone = c["tones"][index]
    parts = [np.zeros(173), signal(tone["a_hz"], tone["a_min"]+.2)]
    if tone["kind"] == "two":
        parts.append(signal(tone["b_hz"], tone["b_min"]+.2))
    parts.append(np.zeros(3200))
    raw = np.concatenate(parts)
    detector = Detector(c)
    found = []
    for i in range(0, len(raw), 421):
        found += detector.feed(raw[i:i+421])
    assert [d.tone_id for d in found] == [tone["id"]]

