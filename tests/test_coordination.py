import copy
import json
import threading
import time
import uuid

import pytest
import requests

from tonepage.config import defaults
from tonepage.coordination import Coordinator, NodeClient, server_for
from tonepage.store import Store


def receiver(c, name="North", coverage="dispatch-channel-1"):
    return {"schema": 1, "instance_id": str(uuid.uuid4()), "boot_id": str(uuid.uuid4()), "site": name,
            "group": c["coordination"]["group"], "coverage": coverage, "clock": time.time()}


def event(node, tone="demo-fire", at=None):
    return {"id": str(uuid.uuid4()), "type": "activation", "instance_id": node["instance_id"], "site": node["site"],
            "at": time.time() if at is None else at, "end": time.time(), "tone_ids": [tone], "agencies": [tone],
            "signature": ["two", 600., 900.] if tone == "demo-fire" else ["long", 1000., None],
            "test": None, "duplicate": False, "allow_cloud": False, "quality": .95}


def setup(tmp_path):
    c = defaults()
    c["integrations"] = [{"id": "notify", "kind": "webhook", "enabled": True, "triggers": ["activation"], "url": "http://127.0.0.1:1"}]
    store = Store(tmp_path)
    return c, store, Coordinator(store, c)


def test_same_page_two_receivers_one_shared_action_and_repage(tmp_path):
    c, s, coordinator = setup(tmp_path)
    a, b = receiver(c), receiver(c, "South")
    for node in (a, b):
        coordinator.registration(node, True)
    at = time.time()-10
    first = event(a, at=at)
    one = coordinator.observation({**a, "event": first})
    two = coordinator.observation({**b, "event": event(b, at=at+.3)})
    assert one["shared_id"] == two["shared_id"]
    assert len(s.recent("jobs")) == 1
    assert coordinator.observation({**a, "event": first})["shared_id"] == one["shared_id"]
    assert len(s.rows("SELECT * FROM observations")) == 2
    repeat = coordinator.observation({**a, "event": event(a, at=at+5)})
    assert repeat["shared_id"] != one["shared_id"]
    assert len(s.recent("jobs")) == 1


def test_unique_remote_page_stack_and_separate_coverage(tmp_path):
    c, s, coordinator = setup(tmp_path)
    a, b = receiver(c), receiver(c, "South", "other-channel")
    for n in (a, b):
        coordinator.registration(n, True)
    at = time.time()-10
    first = coordinator.observation({**a, "event": event(a, at=at)})
    stacked = coordinator.observation({**a, "event": event(a, "demo-all", at+3)})
    other = coordinator.observation({**b, "event": event(b, at=at)})
    assert stacked["shared_id"] == first["shared_id"]
    assert other["shared_id"] != first["shared_id"]
    assert len(s.recent("jobs")) == 3


def test_identity_conflict_wrong_group_and_stale_input(tmp_path):
    c, s, coordinator = setup(tmp_path)
    a = receiver(c)
    coordinator.registration(a, True)
    with pytest.raises(PermissionError):
        coordinator.registration({**a, "boot_id": str(uuid.uuid4())}, True)
    with pytest.raises(PermissionError):
        coordinator.registration({**a, "group": "unrelated"}, True)
    coordinator.observation({**a, "event": event(a, at=time.time()-1000)})
    assert s.recent("jobs") == []


def test_real_http_enrollment_and_durable_node_replay(tmp_path, monkeypatch):
    c, s, coordinator = setup(tmp_path / "server")
    coordinator.c["port"] = 0
    token = "test-only-"+"a"*32
    monkeypatch.setenv("TONEPAGE_GROUP_TOKEN", token)
    server = server_for(coordinator, token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        node_config = copy.deepcopy(c)
        node_config["coordination"].update(enabled=True, url=f"http://127.0.0.1:{server.server_port}")
        node_config["instance_id"] = str(uuid.uuid4())
        node_store = Store(tmp_path / "node")
        client = NodeClient(node_store, node_config)
        client.heartbeat()
        e = event(client.envelope())
        client.observe({"event": e})
        client.observe({"event": e})
        assert node_store.get("shared:"+e["id"])
        assert len(s.recent("jobs")) == 1
        response = requests.post(node_config["coordination"]["url"]+"/heartbeat", json={}, timeout=3)
        assert response.status_code == 401
    finally:
        server.shutdown()
        server.server_close()

