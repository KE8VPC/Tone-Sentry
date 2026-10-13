"""Bounded, asynchronous live dispatch output. Capture never waits for speakers."""
import queue
import threading
import time
import numpy as np
from .playback import resolve_output


class Resampler:
    def __init__(self, source_rate, output_rate):
        self.step = source_rate / output_rate
        self.position = 0.
        self.tail = np.empty(0, dtype=np.float32)

    def feed(self, samples):
        data = np.concatenate((self.tail, samples))
        if len(data) < 2:
            self.tail = data
            return np.empty(0, dtype=np.float32)
        positions = np.arange(self.position, len(data)-1, self.step)
        result = np.interp(positions, np.arange(len(data)), data).astype(np.float32)
        self.position = self.position + len(positions)*self.step - (len(data)-1)
        self.tail = data[-1:].copy()
        return result


class LiveAudio:
    def __init__(self):
        self.status = ''
        self.error_prefix = 'Live audio error:'
        self.condition = threading.Condition()
        self.session = None
        self.closed = False
        self.thread = None

    def start(self, source_rate, selection, label='Live dispatch audio'):
        with self.condition:
            if self.closed:
                return
            if self.session:
                self.session['cancel'].set()
            self.session = dict(rate=source_rate, selection=selection, label=label,
                                audio=queue.Queue(maxsize=25), cancel=threading.Event(),
                                finished=threading.Event())
            self.status = 'Opening '+label.lower()+'…'
            if self.thread is None:
                self.thread = threading.Thread(target=self._worker, daemon=True)
                self.thread.start()
            self.condition.notify_all()

    def feed(self, samples):
        with self.condition:
            session = self.session
        if not session or session['cancel'].is_set() or session['finished'].is_set():
            return
        item = (time.monotonic(), np.asarray(samples, dtype=np.float32).copy())
        try:
            session['audio'].put_nowait(item)
        except queue.Full:
            # Drop oldest playback audio rather than delaying detection or building a backlog.
            try: session['audio'].get_nowait()
            except queue.Empty: pass
            try: session['audio'].put_nowait(item)
            except queue.Full: pass

    def finish(self):
        with self.condition:
            if self.session: self.session['finished'].set()

    def stop(self, wait=False):
        with self.condition:
            if self.session: self.session['cancel'].set()
            self.status = ''
            self.condition.notify_all()
            return not wait or self.condition.wait_for(lambda: self.session is None, timeout=2)

    def _worker(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.session is not None)
                if self.closed: return
                session = self.session
            try:
                self._play(session)
            except Exception as error:
                with self.condition:
                    if self.session is session and not session['cancel'].is_set():
                        self.status = self.error_prefix+' '+str(error)
            finally:
                with self.condition:
                    if self.session is session:
                        self.session = None
                        if not self.status.startswith(self.error_prefix):
                            self.status = ''
                    self.condition.notify_all()

    def _play(self, session):
        import sounddevice as sd
        if session['cancel'].is_set(): return
        index, device = resolve_output(sd, session['selection'])
        rate = int(device['default_samplerate'])
        channels = min(2, int(device['max_output_channels']))
        sd.check_output_settings(device=index, channels=channels, dtype='float32', samplerate=rate)
        if session['cancel'].is_set(): return
        converter = Resampler(session['rate'], rate)
        with sd.OutputStream(device=index, channels=channels, dtype='float32', samplerate=rate) as stream:
            with self.condition:
                if self.session is session and not session['cancel'].is_set():
                    self.status = session['label']+' → '+device['name']
            while not session['cancel'].is_set():
                try: captured, samples = session['audio'].get(timeout=.05)
                except queue.Empty:
                    if session['finished'].is_set(): break
                    continue
                if time.monotonic()-captured > 1.:
                    converter = Resampler(session['rate'], rate)
                    continue
                output = converter.feed(samples)
                if len(output) and not session['cancel'].is_set():
                    stream.write(np.repeat(output[:, None], channels, axis=1))
            if session['cancel'].is_set(): stream.abort()

    def close(self):
        self.stop()
        with self.condition:
            self.closed = True
            self.condition.notify_all()
        if self.thread: self.thread.join(timeout=2)
