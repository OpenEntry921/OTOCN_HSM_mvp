"""Application-level NDN simulation; no real assets or network packets."""

import base64
from contextlib import contextmanager
import hashlib
import json
import os
import sqlite3
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature
from relay.policy import evaluate_policy
from shared.schemas import ExecutionRequest

USERS = {
    "operator": "데모 운영자",
    "reviewer": "데모 검토자",
    "observer": "조회 전용 사용자",
}
ASSETS = {"DUSD": 2, "DETH": 8}
SCENARIOS = [
    "normal",
    "amount_tamper",
    "address_tamper",
    "replay",
    "expired",
    "unsigned",
    "untrusted",
    "relay_compromise",
    "policy",
    "cache",
]


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Blocked(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


class Signer:
    def __init__(self, directory, role):
        path = directory / (role + ".key")
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as f:
                f.write(
                    Ed25519PrivateKey.generate().private_bytes(
                        serialization.Encoding.Raw,
                        serialization.PrivateFormat.Raw,
                        serialization.NoEncryption(),
                    )
                )
        self._key = Ed25519PrivateKey.from_private_bytes(path.read_bytes())
        self.public = self._key.public_key()
        self.role = role

    def sign(self, claims):
        return {
            "claims": claims,
            "signer": self.role,
            "signature": base64.b64encode(self._key.sign(canonical(claims))).decode(),
        }


def verify(envelope, trusted, issuer=None, audience=None, check_time=True):
    require(
        isinstance(envelope, dict) and envelope.get("signature"),
        "서명 또는 독립 승인 증명 누락",
    )
    require(envelope.get("signer") in trusted, "신뢰하지 않는 서명자")
    try:
        trusted[envelope["signer"]].verify(
            base64.b64decode(envelope["signature"], validate=True),
            canonical(envelope["claims"]),
        )
    except (InvalidSignature, ValueError, KeyError, TypeError):
        raise Blocked("암호학적 서명 검증 실패")
    c = envelope["claims"]
    if issuer:
        require(
            c.get("iss") == issuer and c.get("aud") == audience,
            "발급자 또는 대상 서비스 불일치",
        )
        if check_time:
            require(
                c.get("iat", float("inf")) <= time.time() <= c.get("exp", 0),
                "토큰 또는 승인 증명 만료",
            )
    return c


class ApprovalService:
    """Owns approval private key. Relay receives only its public verifier."""

    def __init__(self, signer):
        self._signer = signer
        self.public = signer.public

    def approve(self, tx):
        require(
            tx["requester"] in {"operator", "reviewer"},
            "선택한 데모 사용자에게 승인 권한 없음 (실제 신원 인증 아님)",
        )
        require(tx["network"] == "demo-net", "승인 불가 네트워크")
        now = time.time()
        return self._signer.sign(
            {
                "approval_id": str(uuid.uuid4()),
                "request_id": tx["request_id"],
                "transaction": tx,
                "transaction_hash": digest(tx),
                "iat": now,
                "exp": now + 120,
                "policy_version": "demo-approval-v1",
                "iss": "approval",
                "aud": "endpoint",
                "signer_id": "approval",
            }
        )


class Relay:
    def __init__(self, signer, approval_public):
        self._signer = signer
        self.approval_public = approval_public
        self.public = signer.public

    def authorize(self, tx, approval, expired=False):
        c = verify(approval, {"approval": self.approval_public}, "approval", "endpoint")
        require(c["transaction_hash"] == digest(tx), "승인 거래 불일치")
        # Reuse legacy policy for action and destination; exact amount policy uses integer units.
        decision = evaluate_policy(
            ExecutionRequest(
                request_id=tx["request_id"],
                action=tx["action"],
                target=tx["target"],
                requester=tx["requester"],
            )
        )
        require(decision.allowed, decision.reason)
        require(
            tx["amount_units"] <= 100000 * 10 ** ASSETS[tx["asset"]], "수량 상한 초과"
        )
        return self.issue(tx, approval, expired)

    def issue(self, tx, approval, expired=False):
        now = time.time()
        return self._signer.sign(
            {
                "iss": "relay",
                "aud": "endpoint",
                "iat": now - 10 if expired else now,
                "exp": now - 1 if expired else now + 30,
                "execution_id": tx["request_id"],
                "request_id": tx["request_id"],
                "transaction_hash": digest(tx),
                "approval_id": approval["claims"]["approval_id"],
            }
        )


class Transport(Protocol):
    def publish(self, name, content, signer, freshness=30000): ...
    def fetch(self, name): ...


class MockNDN:
    """Interest/Data adapter. Signed metadata binds content, name and freshness."""

    def __init__(self):
        self.data = {}

    def publish(self, name, content, signer, freshness=30000):
        claims = {
            "name": name,
            "content": content,
            "content_hash": digest(content),
            "FreshnessPeriod": freshness,
            "produced_at": time.time(),
        }
        self.data[name] = signer.sign(claims)
        return self.data[name]

    def fetch(self, name):
        return self.data[name]


def verify_data(packet, name, public, role, namespace, check_time=True):
    c = verify(packet, {role: public})
    require(
        name.startswith(namespace) and c["name"] == name,
        "NDN 이름 공간 또는 이름 불일치",
    )
    require(c["content_hash"] == digest(c["content"]), "NDN 콘텐츠 해시 불일치")
    require(
        not check_time
        or (
            isinstance(c.get("FreshnessPeriod"), int)
            and c["FreshnessPeriod"] >= 0
            and 0
            <= time.time() - c.get("produced_at", 0)
            <= c["FreshnessPeriod"] / 1000
        ),
        "NDN Data freshness 만료",
    )
    content = c["content"]
    tx = content["transaction"]
    require(
        name == namespace + tx["request_id"] + "/" + digest(tx),
        "NDN 이름과 요청 ID·거래 해시 불일치",
    )
    return content


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript("""
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created REAL, transaction_json TEXT, result TEXT);
CREATE TABLE IF NOT EXISTS events(run_id TEXT, seq INTEGER, timestamp REAL, actor TEXT, stage TEXT, status TEXT, reason TEXT, details TEXT, PRIMARY KEY(run_id,seq));
CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, request_id TEXT, hash TEXT, expires REAL);
CREATE TABLE IF NOT EXISTS tokens(id TEXT PRIMARY KEY, hash TEXT, expires REAL);
CREATE TABLE IF NOT EXISTS executions(id TEXT PRIMARY KEY, approval_id TEXT UNIQUE NOT NULL, hash TEXT, state TEXT, result TEXT);
CREATE TABLE IF NOT EXISTS hsm_effects(execution_id TEXT PRIMARY KEY, signature TEXT);
CREATE TABLE IF NOT EXISTS cache(name TEXT PRIMARY KEY, packet TEXT);
""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def event(self, run, actor, stage, status, reason, details=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            n = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE run_id=?", (run,)
            ).fetchone()[0]
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,?,?,?,?)",
                (
                    run,
                    n,
                    time.time(),
                    actor,
                    stage,
                    status,
                    reason,
                    json.dumps(details or {}, ensure_ascii=False),
                ),
            )

    def events(self, run, after=0):
        with self.connect() as db:
            return [
                {**dict(r), "details": json.loads(r["details"])}
                for r in db.execute(
                    "SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq",
                    (run, after),
                )
            ]

    def count(self, execution_id):
        with self.connect() as db:
            return db.execute(
                "SELECT COUNT(*) FROM hsm_effects WHERE execution_id=?", (execution_id,)
            ).fetchone()[0]


class MockHSM:
    def __init__(self, signer):
        self._signer = signer

    def execute_in_transaction(self, db, execution_id, tx):
        signature = self._signer.sign(
            {"simulation": True, "transaction_hash": digest(tx)}
        )["signature"]
        db.execute("INSERT INTO hsm_effects VALUES(?,?)", (execution_id, signature))
        return {
            "status": "success",
            "execution_id": execution_id,
            "mock_signature": signature,
            "simulated": True,
        }


class Endpoint:
    def __init__(self, store, relay_public, approval_public, ndn_public, hsm):
        (
            self.store,
            self.relay_public,
            self.approval_public,
            self.ndn_public,
            self._hsm,
        ) = store, relay_public, approval_public, ndn_public, hsm

    def execute(self, packet, name, emit):
        emit("endpoint", "processing", "Endpoint 독립 검증 중")
        body = verify_data(
            packet,
            name,
            self.ndn_public,
            "request-data",
            "/otocn/demo/requests/",
            check_time=False,
        )
        tx, token, proof = body["transaction"], body["token"], body.get("approval")
        t = verify(
            token, {"relay": self.relay_public}, "relay", "endpoint", check_time=False
        )
        require(
            t["request_id"] == tx["request_id"] and t["transaction_hash"] == digest(tx),
            "실행 토큰과 거래 불일치",
        )
        emit("endpoint", "processing", "Relay 토큰 서명·대상·거래 결합 검증 통과")
        a = verify(
            proof,
            {"approval": self.approval_public},
            "approval",
            "endpoint",
            check_time=False,
        )
        require(
            a["request_id"] == tx["request_id"]
            and a["transaction"] == tx
            and a["transaction_hash"] == digest(tx),
            "독립 승인 거래와 불일치",
        )
        require(t["approval_id"] == a["approval_id"], "승인 ID 불일치")
        eid = t["execution_id"]
        with self.store.connect() as db:
            stored_a = db.execute(
                "SELECT * FROM approvals WHERE id=?", (a["approval_id"],)
            ).fetchone()
            stored_t = db.execute("SELECT * FROM tokens WHERE id=?", (eid,)).fetchone()
            require(
                stored_a is not None and stored_t is not None,
                "서버에 기록되지 않은 승인 또는 실행 토큰",
            )
            require(stored_a["hash"] == digest(tx), "서버 승인 기록과 거래 불일치")
        # Durable claim, then transactional mock side effect + completion.
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM executions WHERE id=?", (eid,)).fetchone()
            if old:
                require(old["hash"] == digest(tx), "동일 실행 ID의 거래 충돌")
                previous = (
                    json.loads(old["result"])
                    if old["state"] == "completed"
                    else {"status": "processing", "execution_id": eid}
                )
            else:
                # Old, authenticated identical requests may read an existing result;
                # only a new execution needs current credentials and fresh Data.
                now = time.time()
                require(
                    t["iat"] <= now <= t["exp"] and a["iat"] <= now <= a["exp"],
                    "토큰 또는 승인 증명 만료",
                )
                require(
                    now <= min(stored_a["expires"], stored_t["expires"]),
                    "서버 기록 기준 만료",
                )
                verify_data(
                    packet,
                    name,
                    self.ndn_public,
                    "request-data",
                    "/otocn/demo/requests/",
                )
                require(
                    db.execute(
                        "SELECT 1 FROM executions WHERE approval_id=?",
                        (a["approval_id"],),
                    ).fetchone()
                    is None,
                    "동일 승인 증명의 재사용 차단",
                )
                db.execute(
                    "INSERT INTO executions VALUES(?,?,?,?,?)",
                    (eid, a["approval_id"], digest(tx), "processing", None),
                )
        if old:
            emit(
                "endpoint",
                "passed" if previous["status"] == "success" else "processing",
                "기존 실행 결과 반환 · 추가 실행 없음"
                if previous["status"] == "success"
                else "기존 요청 처리 중",
                previous,
            )
            return previous
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            result = self._hsm.execute_in_transaction(db, eid, tx)
            db.execute(
                "UPDATE executions SET state='completed',result=? WHERE id=?",
                (json.dumps(result), eid),
            )
        emit(
            "endpoint",
            "passed",
            "독립 승인·무결성·중복 검사 통과 · HSM 모의 실행 1회",
            result,
        )
        return result


def normalize(data):
    required = ["requester", "asset", "network", "amount", "target", "scenario"]
    if not isinstance(data, dict) or any(
        not isinstance(data.get(k), str) or not data[k].strip() for k in required
    ):
        raise ValueError("필수 입력은 비어 있지 않은 문자열이어야 합니다")
    if (
        data["requester"] not in USERS
        or data["asset"] not in ASSETS
        or data["network"] != "demo-net"
        or data["scenario"] not in SCENARIOS
    ):
        raise ValueError("허용되지 않은 사용자·자산·네트워크·시나리오")
    if len(data["amount"]) > 80 or len(data["target"]) > 160:
        raise ValueError("입력 길이 초과")
    try:
        amount = Decimal(data["amount"])
        if not amount.is_finite() or amount <= 0 or amount > Decimal("1000000000"):
            raise ValueError("수량은 유한한 양수여야 합니다")
        places = ASSETS[data["asset"]]
        if amount.as_tuple().exponent < -places:
            raise ValueError("자산별 허용 소수점 초과")
        units = amount * (10**places)
        if units != units.to_integral_value():
            raise ValueError("자산별 허용 소수점 초과")
    except InvalidOperation:
        raise ValueError("올바른 수량을 입력하세요")
    return {
        "request_id": str(uuid.uuid4()),
        "requester": data["requester"],
        "asset": data["asset"],
        "network": data["network"],
        "amount_units": int(units),
        "amount": format(amount.quantize(Decimal(1).scaleb(-places)), "f"),
        "target": data["target"].strip(),
        "action": "approve_transfer",
    }


class Engine:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.store = Store(directory / "demo.sqlite3")
        self.approval = ApprovalService(Signer(directory, "approval"))
        self.relay = Relay(Signer(directory, "relay"), self.approval.public)
        self.request_signer = Signer(directory, "request-data")
        self.result_signer = Signer(directory, "result-data")
        self.unknown_signer = Signer(directory, "untrusted-data")
        self.endpoint = Endpoint(
            self.store,
            self.relay.public,
            self.approval.public,
            self.request_signer.public,
            MockHSM(Signer(directory, "mock-hsm")),
        )
        self.transport: Transport = MockNDN()

    def create(self, data):
        tx = normalize(data)
        run = tx["request_id"]
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO runs VALUES(?,?,?,NULL)",
                (run, time.time(), json.dumps(tx)),
            )
        return run, tx

    def process(self, run, tx, scenario):
        started = time.monotonic()
        stage = "application"
        approved = None

        def emit(s, status, reason, details=None):
            self.store.event(run, s, s, status, reason, details)

        try:
            emit(stage, "passed", "서버가 고유 요청 ID 생성 · 수량 정규화", tx)
            stage = "approval"
            emit(stage, "processing", "독립 승인 조건 검사")
            proof = self.approval.approve(tx)
            approved = tx.copy()
            a = proof["claims"]
            with self.store.connect() as db:
                db.execute(
                    "INSERT INTO approvals VALUES(?,?,?,?)",
                    (a["approval_id"], run, digest(tx), a["exp"]),
                )
            emit(stage, "passed", "별도 Ed25519 키로 독립 승인 증명 발급", a)
            stage = "relay"
            emit(stage, "processing", "기존 정책 및 독립 승인 검증")
            wire = tx.copy()
            if scenario == "policy":
                wire["target"] = "not-allowed"
            # Policy scenario obtains a valid proof for a forbidden destination so policy itself rejects.
            if scenario == "policy":
                policy_proof = self.approval.approve(wire)
                self.relay.authorize(wire, policy_proof)
            token = self.relay.authorize(tx, proof, scenario == "expired")
            if scenario in {"amount_tamper", "relay_compromise"}:
                wire["amount_units"] += 1
                wire["amount"] = format(
                    Decimal(wire["amount_units"]) / 10 ** ASSETS[wire["asset"]], "f"
                )
            if scenario == "address_tamper":
                wire["target"] = (
                    "wallet_B" if tx["target"] != "wallet_B" else "wallet_A"
                )
            if scenario == "relay_compromise":
                token = self.relay.issue(wire, proof)
            t = token["claims"]
            with self.store.connect() as db:
                db.execute(
                    "INSERT INTO tokens VALUES(?,?,?)",
                    (t["execution_id"], t["transaction_hash"], t["exp"]),
                )
            emit(
                stage,
                "passed",
                "실행 토큰 발급 (전체 토큰 비공개)",
                {
                    "claims": t,
                    "token_fingerprint": digest(token)[:16],
                    "attack_scope": "Relay 키 탈취·요청 변조 가정, 독립 승인 서비스와 Endpoint는 정상"
                    if scenario == "relay_compromise"
                    else None,
                },
            )
            stage = "ndn"
            name = "/otocn/demo/requests/" + run + "/" + digest(wire)
            body = {"transaction": wire, "approval": proof, "token": token}
            packet = self.transport.publish(
                name,
                body,
                self.unknown_signer if scenario == "untrusted" else self.request_signer,
            )
            if scenario == "unsigned":
                packet.pop("signature")
            emit(
                stage,
                "processing",
                "Endpoint → 실행 요청 Interest",
                {
                    "packet_type": "Interest",
                    "name": name,
                    "nonce": uuid.uuid4().hex[:8],
                    "cache": False,
                },
            )
            packet = self.transport.fetch(name)
            emit(
                stage,
                "processing",
                "Relay → 실행 요청 Data (검증 전)",
                self.packet_view(packet, False),
            )
            stage = "endpoint"
            result = self.endpoint.execute(packet, name, emit)
            emit(
                "ndn",
                "passed",
                "실행 요청 Data 검증 통과",
                self.packet_view(packet, False),
            )
            if scenario == "replay":
                emit(
                    "ndn",
                    "processing",
                    "동일 실행 요청 재전송 · 새 Interest Nonce",
                    {"nonce": uuid.uuid4().hex[:8], "name": name},
                )
                result = self.endpoint.execute(packet, name, emit)
            stage = "ndn"
            result_name = "/otocn/demo/results/" + run + "/" + digest(wire)
            result_packet = self.transport.publish(
                result_name, {"transaction": wire, "result": result}, self.result_signer
            )
            with self.store.connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO cache VALUES(?,?)",
                    (result_name, json.dumps(result_packet)),
                )
            emit(
                stage,
                "processing",
                "Relay → 실행 결과 Interest",
                {
                    "packet_type": "Interest",
                    "name": result_name,
                    "nonce": uuid.uuid4().hex[:8],
                },
            )
            result_packet = self.transport.fetch(result_name)
            verify_data(
                result_packet,
                result_name,
                self.result_signer.public,
                "result-data",
                "/otocn/demo/results/",
            )
            emit(
                stage,
                "passed",
                "Endpoint → 실행 결과 Data 검증 통과",
                self.packet_view(result_packet, False),
            )
            if scenario == "cache":
                with self.store.connect() as db:
                    cached = json.loads(
                        db.execute(
                            "SELECT packet FROM cache WHERE name=?", (result_name,)
                        ).fetchone()[0]
                    )
                result = verify_data(
                    cached,
                    result_name,
                    self.result_signer.public,
                    "result-data",
                    "/otocn/demo/results/",
                )["result"]
                emit(
                    stage,
                    "passed",
                    "캐시된 결과 Data 검증·재표시 · 실행기 호출 없음",
                    self.packet_view(cached, True),
                )
            final = {
                **result,
                "reason": "모의 실행 완료"
                if result["status"] == "success"
                else "기존 요청 처리 중",
            }
        except Blocked as exc:
            emit(stage, "blocked", str(exc))
            final = {"status": "blocked", "blocked_stage": stage, "reason": str(exc)}
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Web demo processing failed at stage %s for run %s", stage, run
            )
            emit(stage, "error", "시스템 오류 · 성공 여부를 확인할 수 없음")
            final = {
                "status": "error",
                "blocked_stage": stage,
                "reason": "시스템 오류. 서버 기록을 확인하세요",
            }
        final.update(
            request_id=run,
            approved_transaction=approved,
            execution_count=self.store.count(run),
            duration_ms=round((time.monotonic() - started) * 1000, 2),
        )
        emit(
            "audit",
            "passed" if final["status"] == "success" else final["status"],
            "실행 결과 영속 저장",
            final,
        )
        with self.store.connect() as db:
            db.execute(
                "UPDATE runs SET result=? WHERE id=?",
                (json.dumps(final, ensure_ascii=False), run),
            )

    @staticmethod
    def packet_view(packet, cached):
        c = packet["claims"]
        return {
            k: c[k] for k in ["name", "content_hash", "FreshnessPeriod", "produced_at"]
        } | {
            "packet_type": "Data",
            "signer": packet["signer"],
            "cache": cached,
            "signature_present": bool(packet.get("signature")),
        }

    def get(self, run):
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run,)).fetchone()
        if row is None:
            return None
        return {
            "request_id": run,
            "transaction": json.loads(row["transaction_json"]),
            "result": json.loads(row["result"]) if row["result"] else None,
            "events": self.store.events(run),
        }
