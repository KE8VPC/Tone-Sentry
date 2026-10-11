from .storage_paths import audio_root, managed_audio
"""Local advisory audio capture; never participates in alert delivery."""
import collections
import shutil
import uuid
import wave
import numpy as np

AUDIO_DEFAULTS = dict(record_enabled=False, audio_pre_roll=2., audio_silence_seconds=3.,
                      audio_silence_rms=.012, audio_min_seconds=4., audio_post_roll=1., audio_max_seconds=90.)


class DiscoveryRecorder:
    def __init__(self, engine):
        self.engine = engine
        self.settings = dict(AUDIO_DEFAULTS, **engine.config.get('discovery', {}))
        self.pre = collections.deque()
        self.pre_count = 0
        self.active = None
        self.recent = collections.deque(maxlen=16)
        self.last_voice = 0.
        self.last_tone = 0.
        self.cooldown = False

    def reset(self, interrupted=False):
        self.finish(interrupted=interrupted)
        self.pre.clear()
        self.pre_count = 0
        self.recent.clear()
        self.cooldown = False
        self.last_voice = self.last_tone = 0.

    def process(self, samples, stamp):
        e, c = self.engine, self.settings
        if not c['record_enabled'] or not e.discovery.settings['enabled']:
            return
        end = stamp + len(samples)/e.rate
        level = float(np.sqrt(np.mean(samples*samples))) if len(samples) else 0.
        if level >= c['audio_silence_rms']:
            self.last_voice = end
        run = e.discovery.current
        stable = run and run['end']-run['start'] >= e.discovery.settings['min_seconds']-e.detector.dt/2
        evidence = stable or e.discovery.runs or e.discovery.ready
        if evidence:
            self.last_tone = end
        quiet = end-self.last_voice >= c['audio_silence_seconds']
        if self.cooldown and quiet:
            self.cooldown = False
        if evidence and not self.active and not self.cooldown:
            self.begin(stamp)
        if self.active:
            a = self.active['data']
            remaining = max(0, round(c['audio_max_seconds']*e.rate)-a['samples'])
            block = samples[:remaining]
            self.write(block)
            a['end'] = stamp+len(block)/e.rate
            if len(block) < len(samples) or a['samples'] >= round(c['audio_max_seconds']*e.rate):
                self.finish(limited=True)
                self.cooldown = True
            elif quiet and not evidence and end-a['trigger_time'] >= c['audio_min_seconds'] and end-self.last_tone >= c['audio_post_roll']:
                # Candidate drain/link happens later in this same processing block.
                self.finish()
        self.pre.append(samples.copy())
        self.pre_count += len(samples)
        maximum = round((c['audio_pre_roll']+e.discovery.settings['min_seconds']+2*e.detector.dt)*e.rate)
        while self.pre and self.pre_count-len(self.pre[0]) >= maximum:
            self.pre_count -= len(self.pre.popleft())

    def begin(self, stamp):
        e = self.engine
        root = audio_root(e.home)
        root.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(root).free < 100*1024*1024:
            raise OSError('Less than 100 MiB free disk space')
        rid = str(uuid.uuid4())
        path = root/(rid+'.wav')
        writer = wave.open(str(path), 'wb')
        writer.setparams((1, 2, e.rate, 0, 'NONE', 'not compressed'))
        pre = np.concatenate(list(self.pre)) if self.pre else np.empty(0, dtype=np.float32)
        data = dict(recording_id=rid, start=stamp-len(pre)/e.rate, end=stamp, trigger_time=stamp,
                    last_detection=stamp, tone_ids=[], agencies=['Unknown tone activity'], detections=[],
                    discovery_only=True, candidate_ids=[], allow_cloud=False, eligible=False,
                    synthetic=e.replay_safe, samples=0, clipped=0, energy=0.,
                    instance_id=e.config['instance_id'], site=e.config['site'])
        data['encoding_settings'] = dict(e.config['recording'])
        self.active = dict(path=path, writer=writer, data=data)
        self.write(pre)
        e.store.recording(rid, data['start'], stamp, 'capturing', path, data)

    def write(self, samples):
        a = self.active['data']
        self.active['writer'].writeframes((samples*32767).astype('<i2').tobytes())
        a['samples'] += len(samples)
        a['clipped'] += int(np.count_nonzero(np.abs(samples) >= .99))
        a['energy'] += float(np.sum(samples*samples))

    def recording_for(self, start, end):
        clips = ([self.active['data']] if self.active else []) + list(reversed(self.recent))
        return next((a['recording_id'] for a in clips if a['start'] <= start+.1 and a['end'] > start and a['start'] < end), None)

    def link(self, candidate_id, rid):
        if self.active and self.active['data']['recording_id'] == rid:
            a = self.active['data']
            if candidate_id not in a['candidate_ids']:
                a['candidate_ids'].append(candidate_id)
            self.engine.store.recording(rid, a['start'], a['end'], 'capturing', self.active['path'], a)

    def finish(self, interrupted=False, limited=False):
        if not self.active: return
        active, self.active = self.active, None
        active['writer'].close()
        a = active['data']
        a.update(interrupted=interrupted, maximum_duration_reached=limited)
        self.recent.append(a)
        self.engine.store.recording(a['recording_id'], a['start'], a['end'], 'encoding', active['path'], a)
        self.engine.store.enqueue('encode:'+a['recording_id'], 'encode', dict(recording_id=a['recording_id'], wav=str(active['path']), data=a))
