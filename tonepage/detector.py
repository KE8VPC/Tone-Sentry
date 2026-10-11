"""Streaming spectral tone tracker and duration-validated paging state machines."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class Detection:
    tone_id: str
    start: float
    end: float
    quality: float


class Detector:
    def __init__(self, config: dict):
        self.rate = config["input"]["sample_rate"]
        self.n = round(self.rate * config["detector"]["frame_ms"] / 1000)
        self.dt = self.n / self.rate
        self.minimum = config["detector"]["min_rms"]
        self.purity = config["detector"]["min_purity"]
        self.tones = [t for t in config["tones"] if t["enabled"]]
        self.window = np.hanning(self.n)
        self.fft_n = 8 * self.n
        self.observer = None
        self.reset()

    def reset(self):
        if self.observer is not None:
            self.observer.reset()
        self.buffer = np.empty(0, dtype=np.float32)
        self.position = 0.0
        self.states = {t["id"]: {"stage": None, "start": 0., "last": 0., "quality": []} for t in self.tones}

    def frequency(self, x, minimum_purity=None):
        x = x - np.mean(x)
        rms = float(np.sqrt(np.mean(x * x)))
        if rms < self.minimum:
            return None, 0.0
        spectrum = np.abs(np.fft.rfft(x * self.window, n=self.fft_n)) ** 2
        lo, hi = int(100 * self.fft_n / self.rate), int(min(3600, self.rate / 2) * self.fft_n / self.rate)
        peak = lo + int(np.argmax(spectrum[lo:hi]))
        # A Hann-windowed sinusoid spreads across its main lobe. Compare that energy
        # with all non-DC energy rather than accepting the loudest speech harmonic.
        radius = 16
        quality = float(spectrum[max(1, peak-radius):peak+radius+1].sum() / max(spectrum[1:].sum(), 1e-20))
        if quality < (self.purity if minimum_purity is None else minimum_purity):
            return None, quality
        delta = 0.0
        if 0 < peak < len(spectrum)-1:
            a, b, c = np.log(np.maximum(spectrum[peak-1:peak+2], 1e-30))
            divisor = a - 2*b + c
            if divisor:
                delta = float(0.5*(a-c)/divisor)
        return (peak + delta) * self.rate / self.fft_n, quality

    def feed(self, samples, start: float | None = None) -> list[Detection]:
        if start is not None and not len(self.buffer):
            self.position = start
        self.buffer = np.concatenate((self.buffer, np.asarray(samples, dtype=np.float32)))
        results = []
        while len(self.buffer) >= self.n:
            frame, self.buffer = self.buffer[:self.n], self.buffer[self.n:]
            freq, quality = self.frequency(frame, minimum_purity=0)
            now = self.position
            self.position += self.dt
            if self.observer is not None:
                self.observer.step(freq, quality, now)
            if quality < self.purity:
                freq = None
            for tone in self.tones:
                match = None
                if freq is not None:
                    a_tolerance = tone["a_hz"]*tone["tolerance_percent"] if tone.get("tolerance_percent") is not None else tone["tolerance_hz"]
                    b_tolerance = tone.get("b_hz",0)*tone["tolerance_percent"] if tone.get("tolerance_percent") is not None else tone["tolerance_hz"]
                    if abs(freq-tone["a_hz"]) <= a_tolerance:
                        match = "a"
                    elif tone["kind"] == "two" and abs(freq-tone["b_hz"]) <= b_tolerance:
                        match = "b"
                self._step(tone, match, now, quality, results)
        return results

    def _step(self, t, match, now, q, out):
        s = self.states[t["id"]]
        stage = s["stage"]
        if stage == "blocked":
            if match is None:
                s["stage"] = None
            return
        if stage is None:
            if match == "a":
                s.update(stage="a", start=now, last=now+self.dt, quality=[q])
            return
        if stage in ("a", "b"):
            if match == stage:
                s["last"] = now+self.dt
                s["quality"].append(q)
                if s["last"]-s["start"] > t[f"{stage}_max"] + self.dt/2:
                    s["stage"] = "blocked"
                return
            duration = s["last"]-s["start"]
            valid = t[f"{stage}_min"]-self.dt/2 <= duration <= t[f"{stage}_max"]+self.dt/2
            if stage == "b" or t["kind"] == "long":
                if valid:
                    out.append(Detection(t["id"], s.get("sequence_start", s["start"]) if stage == "b" else s["start"], s["last"], float(np.mean(s["quality"]))))
                s["stage"] = None
                if match == "a":
                    s.update(stage="a", start=now, last=now+self.dt, quality=[q])
                return
            if valid:
                s.update(stage="gap", sequence_start=s["start"], a_end=s["last"])
            else:
                s["stage"] = None
                return
        if s["stage"] == "gap":
            if now-s["a_end"] > t["gap_max"]+self.dt/2 or match == "a":
                s["stage"] = None
                if match == "a":
                    s.update(stage="a", start=now, last=now+self.dt, quality=[q])
            elif match == "b":
                s.update(stage="b", start=now, last=now+self.dt)
                s["quality"].append(q)
