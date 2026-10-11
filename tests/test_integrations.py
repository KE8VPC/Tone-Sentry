import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tonepage.config import defaults
from tonepage.integrations import JobWorker, queue_actions
from tonepage.store import Store


def test_webhook_real_delivery_idempotency_and_no_local_path(tmp_path):
    received = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append((dict(self.headers), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            self.send_response(204)
            self.end_headers()
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        c = defaults()
        c["integrations"] = [{"id": "hook", "kind": "webhook", "enabled": True, "url": f"http://127.0.0.1:{server.server_port}", "triggers": ["activation"]}]
        s = Store(tmp_path)
        e = {"id": "event-1", "type": "activation", "tone_ids": ["demo-fire"], "path": "private-file", "text": "private-transcript"}
        queue_actions(s, c, e)
        queue_actions(s, c, e)
        worker = JobWorker(s, c)
        assert worker.run_one()
        assert not worker.run_one()
        assert len(received) == 1
        assert "path" not in received[0][1] and "text" not in received[0][1]
        assert received[0][0]["Idempotency-Key"] == "action:event-1:hook"
    finally:
        server.shutdown()
        server.server_close()


def test_test_duplicate_and_cloud_sharing_suppression(tmp_path):
    c = defaults()
    c["integrations"] = [{"id": "transcribe", "kind": "transcription", "enabled": True, "url": "http://127.0.0.1:1"}]
    s = Store(tmp_path)
    for extra in ({"test": "ignore", "allow_cloud": True}, {"duplicate": True, "allow_cloud": True}, {"allow_cloud": False}):
        queue_actions(s, c, {"id": str(extra), "type": "recording_complete", **extra})
    assert s.recent("jobs") == []


def test_transcription_real_multipart_and_transcript_webhook(tmp_path):
    bodies = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            bodies.append((self.path, self.headers.get("Content-Type"), raw))
            response = b'{"text":"Synthetic dispatch transcript."}' if self.path == "/transcribe" else b'{}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        c = defaults()
        base = f"http://127.0.0.1:{server.server_port}"
        c["integrations"] = [
            {"id": "transcribe", "kind": "transcription", "enabled": True, "scope": "local", "url": base+"/transcribe", "daily_limit": 1},
            {"id": "local-hook", "kind": "webhook", "enabled": True, "scope": "local", "url": base+"/notify", "include_transcript": True, "triggers": ["transcript_complete"]},
            {"id": "shared-hook", "kind": "webhook", "enabled": True, "scope": "shared", "url": base+"/must-not-send", "triggers": ["transcript_complete"]}]
        s = Store(tmp_path)
        folder = tmp_path / "recordings"
        folder.mkdir()
        path = folder / "input.mp3"
        path.write_bytes(b"ID3"+b"fixture"*100)
        event = {"id": "recording-1:complete", "recording_id": "recording-1", "type": "recording_complete", "allow_cloud": True, "path": str(path)}
        queue_actions(s, c, event, "local")
        worker = JobWorker(s, c)
        while worker.run_one():
            pass
        assert [b[0] for b in bodies] == ["/transcribe", "/notify"]
        assert bodies[0][1].startswith("multipart/form-data;")
        assert b'name="file"' in bodies[0][2]
        assert json.loads(bodies[1][2])["text"] == "Synthetic dispatch transcript."
        assert s.recent("transcripts")[0]["text"] == "Synthetic dispatch transcript."
        queue_actions(s, c, dict(event, id="recording-2:complete"), "local")
        worker.run_one()
        assert s.recent("jobs")[0]["status"] == "failed"
        assert len(bodies) == 2
    finally:
        server.shutdown()
        server.server_close()


def test_webhook_signing_and_retry_after(tmp_path, monkeypatch):
    import hashlib
    import hmac
    captured = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            captured.append((dict(self.headers), raw))
            self.send_response(429)
            self.send_header("Retry-After", "120")
            self.end_headers()
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("TEST_SIGNING_KEY", "synthetic-secret")
        c = defaults()
        c["integrations"] = [{"id": "hook", "kind": "webhook", "enabled": True, "url": f"http://127.0.0.1:{server.server_port}", "hmac_env": "TEST_SIGNING_KEY"}]
        s = Store(tmp_path)
        queue_actions(s, c, {"id": "one", "type": "recording_complete"})
        before = time.time()
        JobWorker(s, c).run_one()
        headers, raw = captured[0]
        expected = hmac.new(b"synthetic-secret", headers["X-TonePage-Timestamp"].encode()+b"."+raw, hashlib.sha256).hexdigest()
        assert headers["X-TonePage-Signature"] == expected
        job = s.recent("jobs")[0]
        assert job["status"] == "pending" and job["due"] >= before+119
        assert "synthetic-secret" not in json.dumps(job)
    finally:
        server.shutdown()
        server.server_close()
