"""Optional single-authority receiver coordinator and durable outbound node client."""
from __future__ import annotations

from .storage_paths import audio_root, managed_audio

import base64
import hashlib
import hmac
import json
import math
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .integrations import PermanentError, RetryError, JobWorker, post, secret, queue_actions


class NodeClient:
    def __init__(self, store, config):
        self.store, self.config = store, config
        self.c = config["coordination"]
        self.boot = str(uuid.uuid4())
        self.stopped = threading.Event()
        self.thread = None
        self.status = "Not connected"
        self.health_provider = lambda: {}

    def envelope(self):
        return {"schema": 1, "instance_id": self.config["instance_id"], "boot_id": self.boot,
                "site": self.config["site"], "group": self.c["group"], "coverage": self.c["coverage"]}

    def send(self, route, payload):
        response = post(self.c["url"].rstrip("/")+route, json={**self.envelope(), **payload},
                        headers={"Authorization": "Bearer " + secret(self.c["token_env"])})
        return response.json()

    def heartbeat(self):
        try:
            reply = self.send("/heartbeat", {"clock": time.time(), "health": self.health_provider()})
            self.store.set("receiver_roster", reply.get("receivers", []))
            self.status = "Connected"
        except PermanentError:
            self.status = "Registration/authentication conflict; inspect coordinator"
            # A normal restart has a new boot ID; the previous heartbeat lease
            # must expire before it may reclaim this persistent instance ID.
            raise RetryError("Receiver enrollment unavailable; check credentials or duplicate identity", 45) from None
        except Exception:
            self.status = "Offline; shared actions queued"
            raise

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stopped.clear()
        def loop():
            while not self.stopped.is_set():
                try:
                    self.heartbeat()
                except Exception:
                    pass
                self.stopped.wait(self.c["heartbeat_seconds"])
        self.thread = threading.Thread(target=loop, daemon=True, name="coordinator-heartbeat")
        self.thread.start()

    def observe(self, payload):
        # Registration must be live before sending spooled observations.
        self.heartbeat()
        reply = self.send("/observe", {"event": payload["event"]})
        self.store.set("shared:"+payload["event"]["id"], reply["shared_id"])

    def recording(self, payload):
        event = payload["event"]
        ids = [d["id"] for d in event["detections"]]
        if any(self.store.get("shared:"+oid) is None for oid in ids):
            raise RetryError("Waiting for observation acknowledgement", 5)
        path = Path(event["path"]).resolve()
        if not managed_audio(self.store.home,path):
            raise PermanentError("Recording outside managed directory")
        if path.stat().st_size > 20_000_000:
            raise PermanentError("Coordination upload exceeds 20 MB limit")
        self.heartbeat()
        # Coordination archive is an explicitly enrolled trusted receiver group.
        self.send("/recording", {"event": event, "audio": base64.b64encode(path.read_bytes()).decode("ascii")})

    def stop(self):
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=2)


class Coordinator:
    def __init__(self, store, config):
        self.store, self.config = store, config
        self.c = config["coordinator"]
        self.tones = {t["id"]: t for t in config["tones"]}
        self.guard = threading.RLock()
        self.stopped = threading.Event()
        self.worker = JobWorker(store, config)
        self.store.db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes(instance TEXT PRIMARY KEY,boot TEXT,seen REAL,group_id TEXT,coverage TEXT,site TEXT,clock_offset REAL);
        CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,instance TEXT,shared_id TEXT,at REAL,data TEXT);
        CREATE TABLE IF NOT EXISTS shared(id TEXT PRIMARY KEY,group_id TEXT,coverage TEXT,at REAL,data TEXT);
        CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY,shared_id TEXT,received REAL,score REAL,data TEXT);
        """)
        self.store.db.commit()
        self.store.recover()

    def registration(self, body, heartbeat=False):
        for k in ("instance_id", "boot_id"):
            uuid.UUID(body[k])
        if body.get("schema") != 1:
            raise ValueError("Unsupported protocol")
        if body["instance_id"] in self.c.get("revoked_instances", []):
            raise PermissionError("Receiver revoked")
        allowed = self.c.get("allowed_instances", [])
        if allowed and body["instance_id"] not in allowed:
            raise PermissionError("Receiver not enrolled")
        group, coverage = body["group"], body["coverage"]
        if not all(isinstance(v, str) and 0 < len(v) <= 100 for v in (group, coverage, body["site"])):
            raise ValueError("Invalid receiver identity")
        # One group per endpoint. Separate token/endpoint for a different trust group.
        if group != self.config["coordination"]["group"]:
            raise PermissionError("Wrong group")
        with self.store.transaction() as db:
            node = db.execute("SELECT * FROM nodes WHERE instance=?", (body["instance_id"],)).fetchone()
            if node and node["boot"] != body["boot_id"] and time.time()-node["seen"] < 45:
                raise PermissionError("Instance identity is already active")
            if not heartbeat:
                if not node or node["boot"] != body["boot_id"] or time.time()-node["seen"] >= 45:
                    raise PermissionError("Register before submitting observations")
                if node["group_id"] != group or node["coverage"] != coverage:
                    raise PermissionError("Registration scope mismatch")
            else:
                clock = float(body.get("clock", time.time()))
                if not math.isfinite(clock):
                    raise ValueError("Invalid clock")
                db.execute("INSERT OR REPLACE INTO nodes VALUES(?,?,?,?,?,?,?)", (body["instance_id"], body["boot_id"], time.time(), group, coverage, body["site"], clock-time.time()))
        if heartbeat:
            health = body.get("health", {})
            clean = {k: health[k] for k in ("status", "running", "dropped_blocks") if k in health and isinstance(health[k], (str, bool, int))}
            self.store.set("node-health:"+body["instance_id"], clean)

    def roster(self, group):
        result = []
        for node in self.store.rows("SELECT instance,site,coverage,seen,clock_offset FROM nodes WHERE group_id=? ORDER BY site", (group,)):
            node["state"] = "connected" if time.time()-node["seen"] < 45 else "offline"
            node["health"] = self.store.get("node-health:"+node["instance"], {})
            result.append(node)
        return result

    def observation(self, body):
        with self.guard:
            self.registration(body)
            e = body["event"]
            uuid.UUID(e["id"])
            if e["instance_id"] != body["instance_id"]:
                raise ValueError("Observation identity mismatch")
            known = self.store.rows("SELECT * FROM observations WHERE id=?", (e["id"],))
            if known:
                if known[0]["instance"] != body["instance_id"]:
                    raise PermissionError("Observation ID belongs to another receiver")
                return {"shared_id": known[0]["shared_id"]}
            if len(e["tone_ids"]) != 1 or e["tone_ids"][0] not in self.tones:
                raise ValueError("Tone mapping is not configured at coordinator")
            tid = e["tone_ids"][0]
            tone = self.tones[tid]
            if e["signature"] != [tone["kind"], tone["a_hz"], tone.get("b_hz")]:
                raise ValueError("Tone signature conflicts with coordinator configuration")
            at = float(e["at"])
            if not math.isfinite(at) or at > time.time()+10:
                raise ValueError("Observation timestamp is invalid or in the future")
            late = time.time()-at > self.c["max_age_seconds"]
            from .config import test_mode
            mode = test_mode(tone, at)
            e = dict(e, test=mode, allow_cloud=bool(tone.get("allow_cloud")) and bool(e.get("allow_cloud")),
                     agencies=[tone["agency"]])
            matches = []
            for row in self.store.rows("SELECT * FROM shared WHERE group_id=? AND coverage=? AND ABS(at-?)<=? ORDER BY at",
                                       (body["group"], body["coverage"], at, self.config["recording"]["stack_seconds"])):
                s = json.loads(row["data"])
                prior = [o for o in s["observations"] if o["tone_ids"] == [tid]]
                if prior:
                    if any(o["instance_id"] == e["instance_id"] for o in prior):
                        continue
                    if not any(abs(o["at"]-at) <= self.c["match_seconds"] for o in prior):
                        continue
                if abs(row["at"]-at) <= self.config["recording"]["stack_seconds"]:
                    matches.append((row["id"], s))
            if len(matches) == 1:
                sid, shared = matches[0]
            else:
                sid = str(uuid.uuid4())
                shared = {"id": sid, "at": at, "observations": [], "tone_ids": [], "agencies": [],
                          "eligible_tones": [], "allow_cloud": True, "revision": 0}
            is_new_agency = tid not in shared["tone_ids"]
            shared["observations"].append(e)
            shared["tone_ids"] = sorted(set(shared["tone_ids"]+[tid]))
            shared["agencies"] = sorted(set(shared["agencies"]+[tone["agency"]]))
            shared["allow_cloud"] = shared["allow_cloud"] and e["allow_cloud"]
            shared["revision"] += 1
            duplicate_key = f"global-activation:{body['group']}:{body['coverage']}:{tid}"
            last = self.store.get(duplicate_key)
            suppressed = last is not None and 0 <= at-last < tone["duplicate_seconds"]
            if is_new_agency and mode is None and not late and not suppressed:
                shared["eligible_tones"].append(tid)
            with self.store.transaction() as db:
                if is_new_agency and tid in shared["eligible_tones"]:
                    db.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (duplicate_key, json.dumps(at)))
                db.execute("INSERT OR REPLACE INTO shared VALUES(?,?,?,?,?)", (sid, body["group"], body["coverage"], shared["at"], json.dumps(shared)))
                db.execute("INSERT INTO observations VALUES(?,?,?,?,?)", (e["id"], e["instance_id"], sid, at, json.dumps(e)))
            self.reconcile_actions()
            return {"shared_id": sid, "late": late}

    def recording(self, body):
        with self.guard:
            self.registration(body)
            event = body["event"]
            rid = str(uuid.UUID(event["recording_id"]))
            if event["instance_id"] != body["instance_id"]:
                raise ValueError("Recording identity mismatch")
            observed = [d["id"] for d in event["detections"]]
            shared_ids = set()
            for oid in observed:
                rows = self.store.rows("SELECT * FROM observations WHERE id=? AND instance=?", (oid, body["instance_id"]))
                if not rows:
                    raise ValueError("Recording references an unacknowledged observation")
                shared_ids.add(rows[0]["shared_id"])
            if not shared_ids:
                raise ValueError("Recording has no observations")
            audio = base64.b64decode(body["audio"], validate=True)
            if not 32 <= len(audio) <= 20_000_000 or hashlib.sha256(audio).hexdigest() != event["sha256"]:
                raise ValueError("Recording integrity/size check failed")
            root = self.store.home / "recordings" / body["instance_id"]
            root.mkdir(parents=True, exist_ok=True)
            path = root / (rid+".mp3")
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != event["sha256"]:
                raise ValueError("Immutable recording ID conflict")
            if not path.exists():
                temp = root / (rid+".part")
                temp.write_bytes(audio)
                temp.replace(path)
            data = dict(event, path=str(path), filename=path.name)
            score = float(data.get("quality", 0))
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("Invalid recording quality")
            self.store.recording(rid, data["start"], data["end"], "complete", path, data)
            with self.store.transaction() as db:
                for sid in shared_ids:
                    db.execute("INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?)", (rid+":"+sid, sid, time.time(), score, json.dumps(data)))
            return {"stored": True, "recording_id": rid}

    def reconcile_actions(self):
        # Durable event state is the outbox source, so crashes between matching and queueing recover.
        with self.guard:
            for row in self.store.rows("SELECT * FROM shared ORDER BY at DESC LIMIT 2000"):
                s = json.loads(row["data"])
                for tid in s["eligible_tones"]:
                    observation = next(o for o in s["observations"] if tid in o["tone_ids"])
                    event = dict(observation, id=f"{s['id']}:activation:{tid}", shared_id=s["id"], duplicate=False, test=None)
                    queue_actions(self.store, self.config, event, "shared")
                candidates = self.store.rows("SELECT * FROM candidates WHERE shared_id=? ORDER BY score DESC,received ASC", (s["id"],))
                if not candidates or time.time()-min(c["received"] for c in candidates) < self.c["selection_wait_seconds"]:
                    continue
                data = json.loads(candidates[0]["data"])
                event = dict(data, id=s["id"]+":complete", shared_id=s["id"], type="recording_complete",
                             tone_ids=s["tone_ids"], agencies=s["agencies"], allow_cloud=s["allow_cloud"] and data.get("allow_cloud", False),
                             duplicate=not bool(s["eligible_tones"]), test=None)
                queue_actions(self.store, self.config, event, "shared")
                self.store.set("preferred:"+s["id"], data["recording_id"])

    def start(self):
        self.worker.start()
        def loop():
            while not self.stopped.wait(1):
                try:
                    self.reconcile_actions()
                except Exception as e:
                    self.store.event("coordination_error", {"message": type(e).__name__})
        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()
        self.worker.stop()


def server_for(coordinator, token):
    if len(token) < 24:
        raise ValueError("Coordinator token must contain at least 24 characters")
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer "+token):
                self.reply(401, {"error": "Authentication required"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 30_000_000:
                    self.reply(413, {"error": "Invalid request size"})
                    return
                self.connection.settimeout(30)
                body = json.loads(self.rfile.read(size))
                if self.path == "/heartbeat":
                    coordinator.registration(body, heartbeat=True)
                    result = {"registered": True, "server_time": time.time(), "receivers": coordinator.roster(body["group"])}
                elif self.path == "/observe":
                    result = coordinator.observation(body)
                elif self.path == "/recording":
                    result = coordinator.recording(body)
                else:
                    self.reply(404, {"error": "Unknown route"})
                    return
                self.reply(200, result)
            except PermissionError:
                self.reply(409, {"error": "Registration conflict or wrong group"})
            except (ValueError, KeyError, TypeError, OverflowError):
                self.reply(400, {"error": "Invalid request or tone mapping"})
            except Exception:
                self.reply(503, {"error": "Coordinator temporarily unavailable"})

        def reply(self, code, data):
            raw = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    return ThreadingHTTPServer((coordinator.c["bind"], coordinator.c["port"]), Handler)
