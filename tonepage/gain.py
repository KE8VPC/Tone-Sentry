"""Conservative tone-assisted AGC; signal-independent overload reduction."""
import math
import numpy as np


class GainControl:
    def __init__(self, gain=1.):
        self.applied = float(gain)
        self.tonal_seconds = 0.
        self.automatic = False

    def process(self, raw, rate, settings, tone_quality=0., tone_present=False):
        manual = float(settings['gain'])
        auto = settings.get('auto_gain',False)
        if not auto:
            self.applied = manual
            self.tonal_seconds = 0.
            self.automatic = False
            return raw*manual
        if not self.automatic:
            self.applied = max(.1,min(8.,manual))
            self.automatic = True
        if not len(raw): return raw
        duration = len(raw)/rate
        peak = float(np.max(np.abs(raw)))
        rms = float(np.sqrt(np.mean(raw*raw)))
        tonal = tone_present and tone_quality>=.75 and rms>=.005
        self.tonal_seconds = self.tonal_seconds+duration if tonal else 0.
        target = max(.1,min(8.,.5/max(peak,1e-8)))
        old = self.applied
        if peak*old>.85:
            # Reduce immediately before output; do not ramp through clipped samples.
            self.applied = min(old,target)
            return raw*self.applied
        if self.tonal_seconds>=.2:
            speed = .15 if target<old else 1.5
            self.applied = old+(target-old)*(1-math.exp(-duration/speed))
        return raw*np.linspace(old,self.applied,len(raw),dtype=np.float32)
