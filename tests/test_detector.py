import copy
import numpy as np
import pytest

from tonepage.config import defaults
from tonepage.demo import signal
from tonepage.detector import Detector


def detect(parts, config=None, chunk=317):
    c = config or defaults()
    d = Detector(c)
    data = np.concatenate(parts+[np.zeros(1600)])
    results = []
    for index in range(0, len(data), chunk):
        results.extend(d.feed(data[index:index+chunk]))
    return results


def test_two_tone_and_long_streaming_arbitrary_chunks():
    results = detect([signal(600, 1), signal(900, 3), np.zeros(3200), signal(1000, 4)])
    assert [d.tone_id for d in results] == ["demo-fire", "demo-all"]
    assert results[0].start == pytest.approx(0, abs=.05)
    assert results[0].end == pytest.approx(4, abs=.05)


@pytest.mark.parametrize("parts", [
    [signal(600, .3), signal(900, 3)],
    [signal(600, 1), signal(900, .4)],
    [signal(600, 2), signal(900, 3)],
    [signal(600, 1), signal(900, 5)],
    [signal(900, 3), signal(600, 1)],
    [signal(600, 1), np.zeros(16000), signal(900, 3)],
    [signal(625, 1), signal(900, 3)],
    [signal(1000, 9)],
    [signal(600, 1, amplitude=.001), signal(900, 3, amplitude=.001)],
])
def test_reject_near_misses(parts):
    assert detect(parts) == []


def test_noise_and_multifrequency_not_a_page():
    rng = np.random.default_rng(22)
    assert detect([rng.normal(0, .15, 16000*15)]) == []
    assert detect([signal(600, 1)+signal(1300, 1), signal(900, 3)+signal(1800, 3)]) == []


def test_close_frequencies_and_reverse_sequences():
    c = defaults()
    t = c["tones"][0]
    t.update(a_hz=349, b_hz=365, tolerance_hz=4, a_min=.5, a_max=5, b_min=.5, b_max=8)
    c["tones"] = [t]
    assert len(detect([signal(349, .8), signal(365, .8)], c)) == 1
    assert detect([signal(365, .8), signal(349, .8)], c) == []

