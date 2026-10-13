"""Short local notification tones using the selected output, off the capture thread."""
import time
import numpy as np
from .live_audio import LiveAudio


class AlertAudio(LiveAudio):
    def __init__(self):
        super().__init__()
        self.error_prefix = 'Alert audio error:'
        self.last = {}
        self.last_any = float('-inf')

    def notify(self, selection, volume=30, key='known', preview=False):
        now = time.monotonic()
        with self.condition:
            if self.closed or self.session is not None:
                return False
            if not preview and (now-self.last_any < 2 or key.startswith('discovery:') and now-self.last.get(key, float('-inf')) < 60):
                return False
            self.last = {k:v for k,v in self.last.items() if now-v < 60}
            self.last[key] = self.last_any = now
            rate = 16000
            t = np.arange(int(rate*.3), dtype=np.float32)/rate
            envelope = np.minimum(1, np.minimum(t/.015, (.3-t)/.025))
            samples = (.35*max(0,min(100,volume))/100*np.sin(2*np.pi*880*t)*envelope).astype(np.float32)
            self.start(rate, selection, label='Alert tone')
            self.feed(samples)
            self.finish()
            return True
