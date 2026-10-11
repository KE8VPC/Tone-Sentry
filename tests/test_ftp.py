import json
import threading
import uuid
import pytest
from pathlib import Path

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from tonepage.config import defaults
from tonepage.integrations import JobWorker, queue_actions
from tonepage.store import Store


@pytest.mark.parametrize('remote_template',[None,'Dispatch-{filename}'])
@pytest.mark.parametrize('stored_password',[False,True])
def test_actual_ftp_transfer_and_duplicate_retry(tmp_path, monkeypatch,remote_template,stored_password):
    remote = tmp_path / "remote"
    remote.mkdir()
    authorizer = DummyAuthorizer()
    authorizer.add_user("test", "synthetic-password", str(remote), perm="elradfmwMT")
    class Handler(FTPHandler):
        pass
    Handler.authorizer = authorizer
    server = FTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(timeout=.1, blocking=True, handle_exit=False), daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("TEST_FTP_PASSWORD", "synthetic-password")
        c = defaults()
        c["integrations"] = [{"id": "ftp-test", "kind": "ftp", "enabled": True, "host": "127.0.0.1", "port": server.socket.getsockname()[1], "username": "test", "password_env": "TEST_FTP_PASSWORD", "directory": "/dispatch"}]
        if remote_template:c['integrations'][0]['remote_filename_template']=remote_template
        if stored_password:
            from tonepage.ftp_credentials import encode_password
            c['integrations'][0]['password_b64']=encode_password('synthetic-password')
            monkeypatch.delenv('TEST_FTP_PASSWORD')
        home = tmp_path / "node"
        folder = home / "recordings"
        folder.mkdir(parents=True)
        path = folder / "dispatch.mp3"
        path.write_bytes(b"synthetic-audio"*1024)
        s = Store(home)
        rid = str(uuid.uuid4())
        event = {"id": rid+":complete", "recording_id": rid, "instance_id": c["instance_id"], "type": "recording_complete", "allow_cloud": True, "path": str(path)}
        queue_actions(s, c, event)
        worker = JobWorker(s, c)
        worker.run_one()
        assert s.recent("jobs")[0]["status"] == "done", s.recent("jobs")
        remote_name='Dispatch-'+path.name if remote_template else path.name
        uploaded = remote / "dispatch" / remote_name
        assert uploaded.read_bytes() == path.read_bytes()
        # Simulate retry after remote acceptance but before local acknowledgement.
        with s.transaction() as db:
            db.execute("UPDATE jobs SET status='pending',due=0")
        worker.run_one()
        assert s.recent("jobs")[0]["status"] == "done"
        assert [p.name for p in uploaded.parent.iterdir()] == [remote_name]
        assert "synthetic-password" not in json.dumps(s.recent("jobs"))
        # A same-sized file owned by another sender must not be mistaken for a retry.
        uploaded.write_bytes(b'X'*path.stat().st_size)
        with s.transaction() as db:
            db.execute("UPDATE jobs SET status='pending',due=0")
        worker.run_one()
        assert s.recent('jobs')[0]['status']=='failed'
        assert uploaded.read_bytes()==b'X'*path.stat().st_size
    finally:
        server.close_all()
        thread.join(timeout=2)

