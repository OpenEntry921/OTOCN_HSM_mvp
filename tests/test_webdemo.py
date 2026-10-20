import concurrent.futures
import copy
import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient
from webdemo.core import Engine, Blocked, normalize, digest, verify_data
from webdemo.app import create_app


def data(scenario="normal", **kw):
    return dict(
        requester="operator",
        asset="DUSD",
        network="demo-net",
        amount="10.00",
        target="wallet_A",
        scenario=scenario,
        **kw,
    )


@pytest.fixture
def engine(tmp_path):
    return Engine(tmp_path)


@pytest.mark.parametrize(
    "scenario,count,status",
    [
        ("normal", 1, "success"),
        ("amount_tamper", 0, "blocked"),
        ("address_tamper", 0, "blocked"),
        ("replay", 1, "success"),
        ("expired", 0, "blocked"),
        ("unsigned", 0, "blocked"),
        ("untrusted", 0, "blocked"),
        ("relay_compromise", 0, "blocked"),
        ("policy", 0, "blocked"),
        ("cache", 1, "success"),
    ],
)
def test_scenarios(engine, scenario, count, status):
    rid, tx = engine.create(data(scenario))
    engine.process(rid, tx, scenario)
    out = engine.get(rid)
    assert out["result"]["status"] == status, out
    assert out["result"]["execution_count"] == count
    assert engine.store.count(rid) == count
    assert [e["seq"] for e in out["events"]] == list(range(1, len(out["events"]) + 1))
    public = json.dumps(out)
    assert '"signature"' not in public and '"token"' not in public
    if scenario == "relay_compromise":
        assert "독립 승인 거래와 불일치" in out["result"]["reason"]
        assert any("Relay 토큰 서명" in e["reason"] for e in out["events"])


@pytest.mark.parametrize(
    "amount", ["0", "-1", "NaN", "Infinity", "1.001", "1.000", "abc", "1e1000", ""]
)
def test_invalid_amount(amount):
    d = data()
    d["amount"] = amount
    with pytest.raises(ValueError):
        normalize(d)


@pytest.mark.parametrize(
    "key", ["requester", "asset", "network", "amount", "target", "scenario"]
)
def test_required(key):
    d = data()
    del d[key]
    with pytest.raises(ValueError):
        normalize(d)


def prepared(engine, tx=None, eid=None):
    if tx is None:
        _, tx = engine.create(data())
    proof = engine.approval.approve(tx)
    token = engine.relay.authorize(tx, proof)
    if eid:
        c = token["claims"].copy()
        c["execution_id"] = eid
        token = engine.relay._signer.sign(c)
    a = proof["claims"]
    t = token["claims"]
    with engine.store.connect() as db:
        db.execute(
            "INSERT INTO approvals VALUES(?,?,?,?)",
            (a["approval_id"], tx["request_id"], digest(tx), a["exp"]),
        )
        db.execute(
            "INSERT OR REPLACE INTO tokens VALUES(?,?,?)",
            (t["execution_id"], t["transaction_hash"], t["exp"]),
        )
    name = "/otocn/demo/requests/" + tx["request_id"] + "/" + digest(tx)
    packet = engine.transport.publish(
        name,
        {"transaction": tx, "token": token, "approval": proof},
        engine.request_signer,
    )
    return tx, packet, name


def test_concurrent_and_restart(engine, tmp_path):
    tx, packet, name = prepared(engine)

    def call(_):
        return engine.endpoint.execute(packet, name, lambda *a: None)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(call, range(12)))
    assert all(r["status"] in {"success", "processing"} for r in results)
    assert engine.store.count(tx["request_id"]) == 1
    restored = Engine(tmp_path)
    assert (
        restored.endpoint.execute(packet, name, lambda *a: None)["status"] == "success"
    )
    assert restored.store.count(tx["request_id"]) == 1


def test_processing_return(engine):
    tx, p, n = prepared(engine)
    with engine.store.connect() as db:
        db.execute(
            "INSERT INTO executions VALUES(?,?,?,?,?)",
            (
                tx["request_id"],
                p["claims"]["content"]["approval"]["claims"]["approval_id"],
                digest(tx),
                "processing",
                None,
            ),
        )
    assert engine.endpoint.execute(p, n, lambda *a: None)["status"] == "processing"
    assert engine.store.count(tx["request_id"]) == 0


def test_execution_id_conflict(engine):
    tx, p, n = prepared(engine)
    engine.endpoint.execute(p, n, lambda *a: None)
    other = copy.deepcopy(tx)
    other["amount_units"] += 1
    other["amount"] = "10.01"
    _, p2, n2 = prepared(engine, other, eid=tx["request_id"])
    with pytest.raises(Blocked, match="거래 충돌"):
        engine.endpoint.execute(p2, n2, lambda *a: None)
    assert engine.store.count(tx["request_id"]) == 1


def test_approval_reuse(engine):
    tx, p, n = prepared(engine)
    engine.endpoint.execute(p, n, lambda *a: None)
    body = copy.deepcopy(p["claims"]["content"])
    c = body["token"]["claims"]
    c["execution_id"] = "another-execution"
    body["token"] = engine.relay._signer.sign(c)
    with engine.store.connect() as db:
        db.execute(
            "INSERT INTO tokens VALUES(?,?,?)",
            ("another-execution", digest(tx), c["exp"]),
        )
    p2 = engine.transport.publish(n, body, engine.request_signer)
    with pytest.raises(Blocked, match="승인 증명의 재사용"):
        engine.endpoint.execute(p2, n, lambda *a: None)
    assert engine.store.count("another-execution") == 0


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("missing", "누락"),
        ("signature", "서명 검증 실패"),
        ("name", "이름"),
        ("expiry", "서버 기록 기준 만료"),
        ("audience", "대상 서비스"),
    ],
)
def test_verification_errors(engine, mutation, reason):
    tx, p, n = prepared(engine)
    body = copy.deepcopy(p["claims"]["content"])
    if mutation == "missing":
        body.pop("approval")
    if mutation == "signature":
        body["token"]["signature"] = "AAAA"
    if mutation == "audience":
        body["token"]["claims"]["aud"] = "other"
        body["token"] = engine.relay._signer.sign(body["token"]["claims"])
    if mutation == "expiry":
        with engine.store.connect() as db:
            db.execute("UPDATE tokens SET expires=0")
    if mutation == "name":
        n = n + "wrong"
    p = engine.transport.publish(n, body, engine.request_signer)
    with pytest.raises(Blocked, match=reason):
        engine.endpoint.execute(p, n, lambda *a: None)
    assert engine.store.count(tx["request_id"]) == 0


def test_hsm_transaction_rolls_back(engine, monkeypatch):
    tx, p, n = prepared(engine)
    original = engine.endpoint._hsm.execute_in_transaction

    def fail(db, eid, tx):
        original(db, eid, tx)
        raise RuntimeError("injected failure")

    monkeypatch.setattr(engine.endpoint._hsm, "execute_in_transaction", fail)
    with pytest.raises(RuntimeError):
        engine.endpoint.execute(p, n, lambda *a: None)
    assert engine.store.count(tx["request_id"]) == 0
    # An interrupted claim remains processing for explicit operator investigation; never auto re-execute.
    assert engine.endpoint.execute(p, n, lambda *a: None)["status"] == "processing"


def test_api_recovery_sse_and_download(tmp_path):
    client = TestClient(create_app(tmp_path))
    assert client.get("/").status_code == 200
    for scenario in ["normal", "relay_compromise"]:
        response = client.post("/api/runs", json=data(scenario))
        assert response.status_code == 202
        rid = response.json()["request_id"]
        out = client.get("/api/runs/" + rid).json()
        sse = client.get(
            "/api/runs/" + rid + "/events", headers={"Last-Event-ID": "2"}
        ).text
        assert "id: 1\n" not in sse and "event: complete" in sse
        for e in out["events"][2:]:
            assert "id: " + str(e["seq"]) + "\n" in sse
        assert client.get("/api/runs/" + rid + "/download").json() == out
        restored = TestClient(create_app(tmp_path))
        assert restored.get("/api/runs/" + rid).json() == out
    assert client.post("/api/runs", json={}).status_code == 422
    assert client.get("/api/runs/missing").status_code == 404


def test_system_error_is_not_blocked(engine, monkeypatch):
    monkeypatch.setattr(
        engine.transport,
        "fetch",
        lambda name: (_ for _ in ()).throw(OSError("network error")),
    )
    rid, tx = engine.create(data())
    engine.process(rid, tx, "normal")
    out = engine.get(rid)["result"]
    assert out["status"] == "error" and out["execution_count"] == 0


def test_access_protection(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_ACCESS_KEY", "test-only-password")
    c = TestClient(create_app(tmp_path))
    assert c.get("/").status_code == 401
    assert c.get("/", auth=("demo", "test-only-password")).status_code == 200


def test_observer_cannot_approve(engine):
    d = data()
    d["requester"] = "observer"
    rid, tx = engine.create(d)
    engine.process(rid, tx, "normal")
    result = engine.get(rid)["result"]
    assert result["status"] == "blocked" and result["blocked_stage"] == "approval"
    assert result["execution_count"] == 0


def test_exact_smallest_unit(engine):
    d = data()
    d.update(asset="DETH", amount="0.00000001")
    rid, tx = engine.create(d)
    assert tx["amount_units"] == 1 and tx["amount"] == "0.00000001"
    engine.process(rid, tx, "normal")
    assert engine.get(rid)["result"]["execution_count"] == 1


def test_relay_amount_limit(engine):
    d = data()
    d["amount"] = "100000.01"
    rid, tx = engine.create(d)
    engine.process(rid, tx, "normal")
    r = engine.get(rid)["result"]
    assert r["blocked_stage"] == "relay" and r["execution_count"] == 0


def test_completed_retry_after_expiry(engine, tmp_path, monkeypatch):
    tx, packet, name = prepared(engine)
    original = engine.endpoint.execute(packet, name, lambda *args: None)
    restarted = Engine(tmp_path)
    future = time.time() + 3600
    monkeypatch.setattr("webdemo.core.time.time", lambda: future)
    assert restarted.endpoint.execute(packet, name, lambda *args: None) == original
    assert restarted.store.count(tx["request_id"]) == 1
