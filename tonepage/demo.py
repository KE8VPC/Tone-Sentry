from pathlib import Path
import wave
import numpy as np


def signal(hz, seconds, rate=16000, amplitude=.35):
    t = np.arange(round(seconds*rate))/rate
    return (amplitude*np.sin(2*np.pi*hz*t)).astype(np.float32)


def write_demo(path: Path, config: dict):
    rate = config["input"]["sample_rate"]
    tones = [t for t in config["tones"] if t["enabled"]]
    if not tones:
        raise ValueError("Enable at least one tone set to create a demo")
    pieces = [np.zeros(rate, dtype=np.float32)]
    chosen = tones[:2]
    for tone in chosen + chosen[:1]:
        pieces.append(signal(tone["a_hz"], min(tone["a_max"]-.08, tone["a_min"]+.2), rate))
        if tone["kind"] == "two":
            pieces.append(signal(tone["b_hz"], min(tone["b_max"]-.08, tone["b_min"]+.2), rate))
        pieces.append(np.zeros(round(.4*rate), dtype=np.float32))
    # Synthetic dispatch-like noise, deliberately not a real spoken incident.
    rng = np.random.default_rng(73)
    pieces.append((rng.normal(0, .06, 3*rate)).astype(np.float32))
    pieces.append(np.zeros(round((config["recording"]["silence_seconds"]+config["recording"]["min_seconds"]+1)*rate), dtype=np.float32))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        f.writeframes((np.concatenate(pieces)*32767).astype("<i2").tobytes())
    return path

