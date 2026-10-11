"""Bounded web commands executed by the desktop owner, never by HTTP threads."""
import copy
import hashlib
import json
import queue
import threading
import time
import uuid
from datetime import datetime

from . import __version__


def revision(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:24]


TONE_FIELDS = {'agency', 'enabled', 'kind', 'a_hz', 'b_hz', 'a_min', 'a_max',
               'b_min', 'b_max', 'gap_max', 'tolerance_hz', 'duplicate_seconds',
               'record_enabled', 'allow_cloud'}


class ReceiverController:
    def __init__(self, owner, busy=lambda: False):
        self.owner, self.busy = owner, busy
        self.queue = queue.Queue(maxsize=32)
        self.lock = threading.RLock()
        self.operations = {}
        self.closed = False
        self.snapshot = {}
        self.publish()

    def publish(self):
        o, e = self.owner, self.owner.engine
        with e.settings_lock:
            snapshot = dict(version=__version__, site=o.config['site'], running=e.running,
                paused=e.detection_paused, status=e.status, recording=bool(e.active or e.discovery_audio.active),
                pending=bool(e.pending_settings), settings_status=e.settings_status,
                input_level=float(e.level), dropped=e.dropped,
                audio_age=None if e.last_audio_at is None else max(0,time.time()-e.last_audio_at),
                input=copy.deepcopy(e.config['input']), revision=revision(o.config),
                tones=[{'id': t['id'], 'tolerance_percent':t.get('tolerance_percent'), **{k: copy.deepcopy(v) for k,v in t.items() if k in TONE_FIELDS}}
                       for t in o.config['tones']],
                receiver_time=datetime.now().astimezone().isoformat(timespec='seconds'), updated=time.time())
        with self.lock:
            self.snapshot = snapshot

    def read(self):
        with self.lock:
            return copy.deepcopy(self.snapshot)

    def submit(self, action, data, actor, key):
        with self.lock:
            if self.closed:
                raise ValueError('Console is shutting down')
            fingerprint = json.dumps([action, data], sort_keys=True)
            cache_key = actor+':'+key
            for op in self.operations.values():
                if op['key'] == cache_key:
                    if op['fingerprint'] != fingerprint:
                        raise ValueError('Request key was already used for a different command')
                    return op['id']
            if len(self.operations) >= 256:
                finished = next((i for i,v in self.operations.items() if v['status'] != 'pending'), None)
                if finished is None:
                    raise ValueError('Too many pending commands')
                del self.operations[finished]
            oid = str(uuid.uuid4())
            op = dict(id=oid, key=cache_key, fingerprint=fingerprint, status='pending', actor=actor)
            try:
                self.queue.put_nowait((oid, action, copy.deepcopy(data)))
            except queue.Full:
                raise ValueError('Receiver command queue is full; try again shortly') from None
            self.operations[oid] = op
            return oid

    def operation(self, oid, actor):
        with self.lock:
            op = self.operations.get(oid)
            if not op or op['actor'] != actor:
                return None
            return {k:v for k,v in op.items() if k not in ('key', 'fingerprint', 'actor')}

    def pump(self):
        # Called on the Tk thread. Desktop actions already execute on this thread.
        try:
            oid, action, data = self.queue.get_nowait()
        except queue.Empty:
            self.publish()
            return
        o, e = self.owner, self.owner.engine
        with self.lock:
            if self.operations[oid]['status'] != 'pending':
                self.publish()
                return
        try:
            if self.closed:
                raise ValueError('Console is shutting down')
            if self.busy() or e.replay_safe:
                raise ValueError('A desktop dialog or replay is open. Close it before making remote changes.')
            result = self.execute(action, data)
            with self.lock:
                self.operations[oid].update(status='applied', result=result)
        except (ValueError, KeyError, TypeError) as exc:
            with self.lock:
                self.operations[oid].update(status='failed', error=str(exc))
        except Exception:
            with self.lock:
                self.operations[oid].update(status='failed', error='Receiver operation failed; check the desktop receiver.')
        with self.lock:
            op = self.operations[oid]
            audit = dict(actor=op['actor'], action=action, operation=oid, result=op['status'])
        e.store.event('web_control', audit)
        self.publish()

    def execute(self, action, data):
        o, e = self.owner, self.owner.engine
        if action == 'start':
            e.start()
        elif action in ('pause', 'resume'):
            e.pause_detection(action == 'pause')
        elif action == 'stop':
            if (e.active or e.discovery_audio.active) and data.get('confirm') is not True:
                raise ValueError('Recording is active. Confirm stop to interrupt it, or use Pause detections.')
            e.stop()
        elif action == 'clear-deleted':
            return dict(cleared=e.store.clear_history('recordings', mode='deleted'))
        elif action in ('save-tone', 'delete-tone'):
            if data.get('revision') != revision(o.config):
                raise ValueError('Settings changed in another window. Reload tones and review your edit.')
            c = copy.deepcopy(o.config)
            tid = data.get('id')
            old = next((t for t in c['tones'] if t['id'] == tid), None)
            if action == 'delete-tone':
                if not old:
                    raise ValueError('Tone no longer exists')
                c['tones'].remove(old)
            else:
                values = data.get('tone')
                if not isinstance(values, dict) or set(values)-TONE_FIELDS:
                    raise ValueError('Unsupported tone fields')
                for field in ('enabled', 'record_enabled', 'allow_cloud'):
                    if field in values and type(values[field]) is not bool:
                        raise ValueError('Tone switches must be true or false')
                if 'agency' in values and (not isinstance(values['agency'], str) or len(values['agency']) > 160):
                    raise ValueError('Agency must be 1–160 characters')
                if tid and not old:
                    raise ValueError('Tone no longer exists')
                if old is None:
                    old = dict(id='web-'+uuid.uuid4().hex[:16], tests=[])
                    c['tones'].append(old)
                # Preserve schedules, per-tone recording overrides and imported tolerance.
                old.update(values)
            o.apply(c)
        else:
            raise ValueError('Unknown receiver command')
        return dict(pending_settings=bool(e.pending_settings))

    def close(self):
        with self.lock:
            self.closed = True
            self.cancel_pending()

    def cancel_pending(self):
        with self.lock:
            for op in self.operations.values():
                if op['status'] == 'pending':
                    op.update(status='failed', error='Console closed before command was applied')
            while True:
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
