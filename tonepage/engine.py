from __future__ import annotations

from .storage_paths import audio_root, managed_audio

import collections
import copy
import hashlib
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .config import safe_name, test_mode
from .detector import Detector
from .integrations import JobWorker, PermanentError, queue_actions
from .store import Store
from .live_settings import LiveSettings


def ffmpeg_exe(config):
    explicit = config["recording"]["ffmpeg"]
    if explicit:
        if not Path(explicit).is_file():
            raise PermanentError("Configured FFmpeg executable does not exist")
        return explicit
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        raise PermanentError("Install FFmpeg or the encoder extra before recording") from None


class Engine(LiveSettings):
    def __init__(self, home: Path, config: dict, store=None):
        config = copy.deepcopy(config)
        self.home, self.config = home.resolve(), config
        self.init_live_settings()
        self.store = store or Store(home)
        self.detector = Detector(config)
        from .discovery import Discovery, Candidates
        self.discovery = Discovery(config.get('discovery', {}), self.detector.dt)
        self.detector.observer = self.discovery
        self.candidates = Candidates(self.store)
        self.rate = config["input"]["sample_rate"]
        from .gain import GainControl
        self.gain_control = GainControl(config['input']['gain'])
        from .discovery_recording import DiscoveryRecorder
        self.discovery_audio = DiscoveryRecorder(self)
        self.tones = {t["id"]: t for t in config["tones"]}
        self.pre = collections.deque()
        self.pre_count = 0
        self.active = None
        self.last_voice = 0
        self.running = False
        self.detection_paused = False
        self.last_audio_at = None
        self.status = "Stopped"
        self.peak_level = 0.
        self.peak_until = 0.
        self.overload_until = 0.
        self.level = 0.
        self.frequency = None
        self.dropped = 0
        self.audio_queue = queue.Queue(maxsize=250)
        self.stop_event = threading.Event()
        self.capture_thread = None
        self.processing_thread = None
        self.position = 0.
        self.base_time = time.time()
        self.candidate_offset = self.base_time
        self.client = None
        self.replay_safe = False
        from .live_audio import LiveAudio
        self.live_audio = LiveAudio()
        self.live_playback_allowed = lambda: True
        handlers = {"encode": self.encode}
        if config["coordination"]["enabled"]:
            from .coordination import NodeClient
            self.client = NodeClient(self.store, config)
            self.client.health_provider = lambda: {"status": self.status, "running": self.running, "dropped_blocks": self.dropped}
            handlers.update(observe=self.client.observe, coordinate_recording=self.client.recording)
        self.store.recover()
        self.worker = JobWorker(self.store, config, handlers)
        self.recover_recordings()
        self.store.reconcile_recordings()

    def recover_recordings(self):
        for row in self.store.rows("SELECT * FROM recordings WHERE status IN ('capturing','encoding')"):
            data = json.loads(row["data"])
            wav = Path(row["path"] or "")
            if wav.is_file() and managed_audio(self.home,wav):
                data["interrupted"] = True
                if data.get('discovery_only'):
                    try:
                        with wave.open(str(wav)) as source:
                            data['samples'] = source.getnframes()
                            data['end'] = data['start']+source.getnframes()/source.getframerate()
                    except (wave.Error, EOFError):
                        pass  # Encoder retains the source and reports an unusable WAV.
                self.store.enqueue("encode:"+row["id"], "encode", {"recording_id": row["id"], "wav": str(wav), "data": data})
            else:
                self.store.event("recording_error", {"recording_id": row["id"], "message": "Interrupted recording source is missing"})

    def start_workers(self):
        if not self.worker.threads:
            self.worker.start()
        if self.client:
            self.client.start()

    def start(self):
        if self.running:
            return
        ffmpeg_exe(self.config)
        self.detector.reset()
        self.discovery_audio.reset()
        self.position, self.base_time = 0., time.time()
        self.pre.clear()
        self.pre_count = 0
        self.audio_queue = queue.Queue(maxsize=250)
        self.stop_event.clear()
        self.running = True
        self.status = "Connecting audio"
        self.start_workers()
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.processing_thread.start()
        self.capture_thread.start()

    def _capture_loop(self):
        import sounddevice as sd
        while not self.stop_event.is_set():
            if self.audio_reconfigure.is_set():
                self.audio_paused.set()
                while self.audio_reconfigure.is_set() and not self.stop_event.wait(.02):
                    pass
                self.audio_paused.clear()
                continue
            with self.settings_lock:
                i = dict(self.config['input'])
                rate = self.rate
                block = max(self.detector.n, round(rate * .04))
            try:
                def callback(data, frames, timing, status):
                    gap = bool(status)
                    try:
                        self.audio_queue.put_nowait((data[:, i["channel"]].copy(), time.time()-frames/rate, gap))
                    except queue.Full:
                        self.dropped += 1
                with sd.InputStream(device=i["device"], channels=i["channel"]+1, samplerate=rate,
                                    dtype="float32", blocksize=block, callback=callback) as stream:
                    self.status = "Monitoring"
                    self.audio_failed.clear()
                    if self.settings_status == 'Settings applied; audio input reconnecting':
                        self.settings_status = 'Settings applied'
                    while not self.stop_event.wait(.25):
                        if self.audio_reconfigure.is_set():
                            break
                        if not stream.active:
                            raise RuntimeError("Audio input stopped")
            except Exception as e:
                self.audio_failed.set()
                self.status = f"Audio unavailable ({type(e).__name__}); retrying"
                from .audio_diagnostics import error_detail
                self.last_audio_error = error_detail(e, i)
                self.store.event("audio_error", {"message": self.status, **self.last_audio_error})
                self.stop_event.wait(3)

    def _process_loop(self):
        last_end, last_dropped = None, self.dropped
        while not self.stop_event.is_set() or not self.audio_queue.empty():
            try:
                samples, stamp, gap = self.audio_queue.get(timeout=.2)
            except queue.Empty:
                with self.settings_lock:
                    if self.pending_settings and self.audio_failed.is_set():
                        # The source has already failed. Do not wait forever for
                        # silence/tone endings that this input cannot deliver.
                        self.finish_recording(interrupted=True)
                        self.discovery_audio.reset(interrupted=True)
                        self.detector.reset()
                        self.last_voice = 0
                    self._apply_pending_settings()
                continue
            try:
                if gap or last_dropped != self.dropped or last_end is not None and abs(stamp-last_end) > .5:
                    self.store.event("audio_gap", {"dropped_blocks": self.dropped})
                    self.finish_recording(interrupted=True)
                    self.discovery_audio.reset(interrupted=True)
                    self.detector.reset()
                    self.pre.clear()
                    self.pre_count = 0
                last_dropped = self.dropped
                block_rate = self.rate
                generation = self.settings_generation
                self.process(samples, stamp)
                last_end = None if generation != self.settings_generation else stamp+len(samples)/block_rate
            except Exception as e:
                self.status = f"Processing error: {type(e).__name__}"
                self.store.event("processing_error", {"message": self.status})
                try:
                    self.finish_recording(interrupted=True)
                    self.discovery_audio.reset(interrupted=True)
                except Exception:
                    pass
        self.finish_recording(interrupted=True)
        self.discovery.finish()
        self.save_candidates(self.candidate_offset)
        self.discovery_audio.finish(interrupted=True)

    def process(self, samples, stamp=None):
        with self.settings_lock:
            self._process_samples(samples, stamp)
            self._apply_pending_settings()

    def pause_detection(self, paused):
        with self.settings_lock:
            if self.detection_paused != paused:
                self.detection_paused = paused
                self.detector.reset()
                self.store.event('detection_paused' if paused else 'detection_resumed', {})

    def _process_samples(self, samples, stamp=None):
        if not self.replay_safe:
            self.last_audio_at = time.time()
        raw = np.asarray(samples, dtype=np.float32)
        amplified = self.gain_control.process(raw,self.rate,self.config['input'],self.discovery.quality,self.discovery.frequency is not None)
        peak = float(np.max(np.abs(amplified))) if len(raw) else 0.
        if peak>=self.peak_level or time.monotonic()>=self.peak_until:
            self.peak_level = peak
            self.peak_until = time.monotonic()+.3
        if peak >= .99 or len(raw) and float(np.max(np.abs(raw))) >= .99:
            self.overload_until = time.monotonic()+1.5
        samples = np.clip(amplified, -1, 1)
        duration = len(samples)/self.rate
        stamp = self.base_time+self.position if stamp is None else stamp
        # Detector's clock is sample-based; wall time is separately attached to observations.
        offset = stamp-self.position
        self.candidate_offset = offset
        detections = [] if self.detection_paused else self.detector.feed(samples, self.position)
        self.discovery_audio.process(samples, stamp)
        self.save_candidates(offset)
        self.level = float(np.sqrt(np.mean(samples*samples))) if len(samples) else 0.
        if self.level >= self.config["recording"]["silence_rms"]:
            self.last_voice = stamp+duration
        for detection in detections:
            self.detect(detection, offset)
        if self.active:
            if not self.replay_safe:
                self.live_audio.feed(samples)
            pcm = (samples*32767).astype("<i2").tobytes()
            self.active["writer"].writeframes(pcm)
            self.active["data"]["end"] = stamp+duration
            self.active["data"]["samples"] += len(samples)
            self.active["data"]["clipped"] += int(np.count_nonzero(np.abs(samples) >= .99))
            self.active["data"]["energy"] += float(np.sum(samples*samples))
            r, a = self.config["recording"], self.active["data"]
            elapsed = stamp+duration-a["trigger_time"]
            since_detection = stamp+duration-a["last_detection"]
            limit = a["samples"]/self.rate >= a.get("record_max_seconds", r["max_seconds"])
            fixed = r["fixed_seconds"] and elapsed >= r["fixed_seconds"] and since_detection >= r["post_roll"]
            silence = not r["fixed_seconds"] and elapsed >= a.get("record_min_seconds", r["min_seconds"]) and stamp+duration-self.last_voice >= r["silence_seconds"] and since_detection >= r["post_roll"]
            if limit:
                previous = dict(a)
                live_started = self.active.get('live_started',False)
                self.finish_recording(continue_live=not self.detection_paused)
                if not self.detection_paused:
                    self.begin_recording(stamp+duration, continuation=previous)
                    self.active['live_started'] = live_started
            elif fixed or silence:
                self.finish_recording()
        self.pre.append(samples.copy())
        self.pre_count += len(samples)
        maximum = round(self.config["recording"]["pre_roll"]*self.rate)
        while self.pre and self.pre_count-len(self.pre[0]) >= maximum:
            self.pre_count -= len(self.pre.popleft())
        self.position += duration

    def save_candidates(self, offset):
        for candidate in self.discovery.drain():
            rid = self.discovery_audio.recording_for(candidate['start']+offset, candidate['end']+offset)
            candidate['recording_id'] = rid
            cid = self.candidates.observe(candidate, 'replay' if self.replay_safe else 'live', offset)
            if rid: self.discovery_audio.link(cid, rid)

    def detect(self, detection, offset):
        t = self.tones[detection.tone_id]
        at, end = offset+detection.start, offset+detection.end
        mode = test_mode(t, at)
        activation_key = ("replay-activation:" if self.replay_safe else "activation:")+t["id"]
        last = self.store.get(activation_key)
        duplicate = last is not None and 0 <= at-last < t["duplicate_seconds"]
        if mode is None and not duplicate:
            self.store.set(activation_key, at)
        oid = str(uuid.uuid4())
        event = {"schema": 1, "id": oid, "type": "activation", "at": at, "end": end,
                 "instance_id": self.config["instance_id"], "site": self.config["site"],
                 "tone_ids": [t["id"]], "agencies": [t["agency"]], "quality": detection.quality,
                 "duplicate": duplicate, "test": "replay" if self.replay_safe else mode, "synthetic": self.replay_safe,
                 "allow_cloud": bool(t.get("allow_cloud", False)),
                 "signature": [t["kind"], t["a_hz"], t.get("b_hz")], "duplicate_seconds": t["duplicate_seconds"]}
        if (mode != "ignore" and t.get("record_enabled", True)) or self.active:
            if mode != "ignore" and t.get("record_enabled", True) and self.active and at-self.active["data"]["last_detection"] > self.config["recording"]["stack_seconds"] and not duplicate:
                self.finish_recording()
            if not self.active:
                self.begin_recording(offset+self.position)
            a = self.active["data"]
            if t.get("record_enabled", True):
                for key in ("min_seconds", "max_seconds"):
                    value = t.get("record_"+key, self.config["recording"][key])
                    a["record_"+key] = max(a.get("record_"+key, value), value)
            a["last_detection"] = end
            a["detections"].append(event)
            a["tone_ids"] = sorted(set(a["tone_ids"]+[t["id"]]))
            a["agencies"] = sorted(set(a["agencies"]+[t["agency"]]))
            a["allow_cloud"] = a["allow_cloud"] and bool(t.get("allow_cloud", False))
            a["eligible"] = a["eligible"] or mode is None and not duplicate and not self.replay_safe
            event["recording_id"] = a["recording_id"]
            self.store.recording(a["recording_id"], a["start"], a["end"], "capturing", self.active["path"], a)
        if (self.active and not self.replay_safe and not self.stop_event.is_set() and mode is None and not duplicate
                and self.config.get('playback',{}).get('live_after_detection',False)
                and self.live_playback_allowed() and not self.active.get('live_started')):
            self.live_audio.start(self.rate, copy.deepcopy(self.config.get('playback',{}).get('device')))
            self.active['live_started'] = True
        self.store.event("detection", event, at, oid)
        if self.replay_safe:
            return
        if self.client:
            self.store.enqueue("observe:"+oid, "observe", {"event": event, "recording_id": event.get("recording_id")})
            queue_actions(self.store, self.delivery_config, event, "local")
        else:
            queue_actions(self.store, self.delivery_config, event)

    def begin_recording(self, stamp, continuation=None):
        rid = str(uuid.uuid4())
        root = audio_root(self.home)
        root.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(root).free < 100*1024*1024:
            raise OSError("Less than 100 MiB free disk space")
        path = root / (rid+".wav")
        writer = wave.open(str(path), "wb")
        writer.setparams((1, 2, self.rate, 0, "NONE", "not compressed"))
        pre = np.concatenate(list(self.pre)) if self.pre and continuation is None else np.empty(0, dtype=np.float32)
        if len(pre):
            writer.writeframes((pre*32767).astype("<i2").tobytes())
        data = {"recording_id": rid, "start": stamp-len(pre)/self.rate, "end": stamp,
                "trigger_time": stamp, "last_detection": stamp, "tone_ids": [], "agencies": [],
                "detections": [], "allow_cloud": True, "eligible": False, "samples": len(pre),
                "clipped": int(np.count_nonzero(np.abs(pre) >= .99)), "energy": float(np.sum(pre*pre)),
                "instance_id": self.config["instance_id"], "site": self.config["site"]}
        data["synthetic"] = self.replay_safe
        data['encoding_settings'] = dict(self.config['recording'])
        if continuation:
            for key in ("tone_ids", "agencies", "allow_cloud", "eligible", "detections", "record_min_seconds", "record_max_seconds"):
                if key not in continuation:
                    continue
                data[key] = continuation[key].copy() if isinstance(continuation[key], list) else continuation[key]
            data["continuation_of"] = continuation["recording_id"]
        self.active = {"path": path, "writer": writer, "data": data}
        self.store.recording(rid, data["start"], stamp, "capturing", path, data)

    def finish_recording(self, interrupted=False, continue_live=False):
        if not self.active:
            return
        if not continue_live:
            self.live_audio.stop() if interrupted else self.live_audio.finish()
        active, self.active = self.active, None
        active["writer"].close()
        data = active["data"]
        data["interrupted"] = interrupted
        self.store.recording(data["recording_id"], data["start"], data["end"], "encoding", active["path"], data)
        self.store.enqueue("encode:"+data["recording_id"], "encode", {"recording_id": data["recording_id"], "wav": str(active["path"]), "data": data})

    def encode(self, payload):
        # Keep encoder/name settings stable even if the UI saves a new configuration.
        config = copy.deepcopy(self.config)
        source = Path(payload["wav"]).resolve()
        if not managed_audio(self.home,source):
            raise PermanentError("Encoding source is outside recording directory")
        data = payload["data"]
        config['recording'] = dict(data.get('encoding_settings', config['recording']))
        from .recording_names import filename_clock
        # Old queued work without an encoding snapshot used UTC. Preserve that choice.
        mode = data.get("encoding_settings", {}).get("filename_timezone", "UTC")
        values = {**filename_clock(data["start"], mode),
                  "agency": "+".join(data["agencies"]), "agencies": "+".join(data["agencies"]),
                  "site": data.get('site',config['site']), "instance": data.get('instance_id',config['instance_id']), "session": data["recording_id"]}
        from .recording_names import reserve_filename
        filename = safe_name(config["recording"]["filename"].format_map(values))
        filename = '_'.join(filename.split())
        target = reserve_filename(self.store,source.parent,filename,data['recording_id'])
        temp = target.with_suffix(".part.mp3")
        if not target.is_file() or target.stat().st_size==0:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            result = subprocess.run([ffmpeg_exe(config), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(source),
                                     "-codec:a", "libmp3lame", "-b:a", config["recording"]["bitrate"], str(temp)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300, creationflags=flags)
            if result.returncode or not temp.is_file() or temp.stat().st_size == 0:
                raise PermanentError("MP3 encoding failed; original WAV retained")
            temp.replace(target)
        data["path"] = str(target)
        data['filename'] = target.name
        data["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        tone_quality = float(np.mean([d.get("quality", 0) for d in data["detections"]])) if data["detections"] else 0
        data["quality"] = tone_quality * max(0, 1-data["clipped"]/max(1, data["samples"])) * (0.5 if data.get("interrupted") else 1)
        sidecar = target.with_suffix(".json")
        sidecar.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.store.recording(data["recording_id"], data["start"], data["end"], "complete", target, data)
        event = dict(data, schema=1, id=data["recording_id"]+":complete", type="recording_complete",
                     at=data["end"], duplicate=not data["eligible"], test=None)
        self.store.event("recording_complete", event, event_id=event["id"])
        if data.get("synthetic") or data.get('discovery_only'):
            source.unlink(missing_ok=True)
            return
        if self.client:
            self.store.enqueue("coordinate-recording:"+data["recording_id"], "coordinate_recording", {"event": event, "recording_id": data["recording_id"]})
            queue_actions(self.store, self.delivery_config, event, "local")
        else:
            queue_actions(self.store, self.delivery_config, event)
        source.unlink(missing_ok=True)

    def replay(self, path: Path, realtime=False):
        ffmpeg_exe(self.config)
        self.replay_safe = True
        self.base_time, self.position = time.time(), 0.
        self.detector.reset()
        self.discovery_audio.reset()
        self.pre.clear()
        self.pre_count = 0
        self.last_voice = self.base_time
        for tid in self.tones:
            self.store.set("replay-activation:"+tid, None)
        self.start_workers()
        self.status, self.running = "Replaying WAV", True
        try:
            with wave.open(str(path), "rb") as f:
                if f.getsampwidth() != 2 or f.getframerate() != self.rate:
                    raise ValueError(f"Replay requires 16-bit PCM WAV at {self.rate} Hz")
                channels = f.getnchannels()
                if self.config["input"]["channel"] >= channels:
                    raise ValueError("Configured input channel is absent in replay")
                while not self.stop_event.is_set():
                    raw = f.readframes(self.detector.n)
                    if not raw:
                        break
                    samples = np.frombuffer(raw, dtype="<i2").reshape(-1, channels)[:, self.config["input"]["channel"]].astype(np.float32)/32768
                    self.process(samples)
                    if realtime:
                        self.stop_event.wait(len(samples)/self.rate)
                self.discovery.finish()
                self.save_candidates(self.base_time)
                self.process(np.zeros(self.detector.n, dtype=np.float32))
            self.finish_recording()
        finally:
            self.finish_recording(interrupted=True)
            self.discovery_audio.finish(interrupted=True)
            self.replay_safe = False
            self.running, self.status = False, "Replay complete"
            with self.settings_lock:
                self._apply_pending_settings()

    def stop(self):
        self.live_audio.stop()
        self.stop_event.set()
        for thread in (self.capture_thread, self.processing_thread):
            if thread:
                thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError('Audio is still stopping; wait before changing its configuration')
        self.running, self.status = False, "Stopped"
        with self.settings_lock:
            self._apply_pending_settings()

    def close(self):
        self.stop()
        self.discovery_audio.finish(interrupted=True)
        if self.client:
            self.client.stop()
        self.worker.stop()
        self.live_audio.close()
