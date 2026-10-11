"""Apply receiver configuration only at processing boundaries."""
import copy
import threading
from .config import validate


class LiveSettings:
    def init_live_settings(self):
        self.settings_lock = threading.RLock()
        self.pending_settings = None
        self.settings_status = ''
        self.audio_reconfigure = threading.Event()
        self.audio_paused = threading.Event()
        self.audio_failed = threading.Event()
        self.settings_generation = 0
        self.delivery_config = copy.deepcopy(self.config)

    def request_settings(self, config, persist):
        from .detector import Detector
        validate(config)
        candidate = copy.deepcopy(config)
        # Build before persistence so invalid runtime settings cannot displace working ones.
        Detector(candidate)
        with self.settings_lock:
            if candidate['coordination'] != self.config['coordination'] or candidate['instance_id'] != self.config['instance_id']:
                raise ValueError('Receiver coordination/identity changes require stopping monitoring first')
            persist(candidate)
            # Queue creation uses a complete snapshot. Previously queued jobs are untouched.
            self.delivery_config = candidate
            self.worker.config = candidate
            runtime_keys = ('input','detector','recording','tones','discovery','site')
            changed = any(candidate.get(k) != self.config.get(k) for k in runtime_keys)
            self.pending_settings = candidate if changed else None
            self.settings_status = 'Settings saved; waiting for the current page/recording to finish' if changed else 'Settings applied for future deliveries'
            if not changed:
                self.audio_reconfigure.clear()
            if not self.running:
                self._apply_pending_settings()

    def settings_boundary_safe(self):
        return (not self.active and not self.discovery_audio.active
                and self.candidate_offset+self.position-self.last_voice >= max(.5, max((t.get('gap_max',0) for t in self.tones.values()),default=0))
                and self.discovery.frequency is None
                and all(s['stage'] is None for s in self.detector.states.values())
                and not self.discovery.current and not self.discovery.runs
                and not self.discovery.ready)

    def _apply_pending_settings(self):
        """Called under settings_lock by the processing thread (or while stopped)."""
        candidate = self.pending_settings
        if candidate is None or self.replay_safe:
            return
        audio_change = any(candidate['input'][k] != self.config['input'][k]
                           for k in ('device','channel','sample_rate'))
        if self.running:
            if not self.settings_boundary_safe():
                # A queued block may start a page after the pause request. Resume the
                # old input to finish it rather than cutting the sequence short.
                self.audio_reconfigure.clear()
                return
            if audio_change:
                self.settings_status = 'Settings pending: reopening audio input between pages (brief reception gap)'
                self.audio_reconfigure.set()
                if not self.audio_paused.is_set() or not self.audio_queue.empty():
                    return
        from .detector import Detector
        from .discovery import Discovery
        from .discovery_recording import DiscoveryRecorder
        detector = Detector(candidate)
        discovery = Discovery(candidate.get('discovery',{}), detector.dt)
        detector.observer = discovery
        self.config = candidate
        if self.client:
            self.client.config = candidate
        self.detector, self.discovery = detector, discovery
        self.tones = {t['id']:t for t in candidate['tones']}
        self.rate = candidate['input']['sample_rate']
        self.discovery_audio = DiscoveryRecorder(self)
        self.pre.clear(); self.pre_count = 0
        self.settings_generation += 1
        self.pending_settings = None
        self.settings_status = 'Settings applied; audio input reconnecting' if audio_change and self.running else 'Settings applied'
        self.store.event('settings_applied', {'message': self.settings_status})
        self.audio_reconfigure.clear()
