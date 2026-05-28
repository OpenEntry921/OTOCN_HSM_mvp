#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from endpoint.service import process_execution
from relay.audit import write_audit
from relay.policy import evaluate_policy
from relay.token_service import issue_token
from shared.schemas import ExecutionRequest

AUDIT_PATH = ROOT / "logs" / "demo_audit.log"


def banner(title: str) -> None:
    print(f"\n=== {title} ===")


def event(message: str, detail: str | None = None) -> None:
    if detail:
        print(f"{message}: {detail}")
    else:
        print(message)


def token_summary(token_info: dict) -> str:
    token = token_info["token"]
    return f"{token[:24]}...{token[-12:]} (expires_at={token_info['expires_at']})"


def request_to_dict(req: ExecutionRequest) -> dict:
    if hasattr(req, "model_dump"):
        return req.model_dump()
    return req.dict()


def issue_request_bound_token(req: ExecutionRequest, ttl_seconds: int = 30) -> dict:
    return issue_token(
        {
            "request_id": req.request_id,
            "action": req.action,
            "target": req.target,
            "amount": req.amount,
            "requester": req.requester,
        },
        ttl_seconds=ttl_seconds,
    )


def relay_authorize(req: ExecutionRequest, ttl_seconds: int = 30) -> dict | None:
    event("REQUEST RECEIVED", f"{req.request_id} amount={req.amount} destination={req.target}")
    write_audit(
        {
            "stage": "request_received",
            "request_id": req.request_id,
            "action": req.action,
            "target": req.target,
            "amount": req.amount,
            "requester": req.requester,
        },
        path=str(AUDIT_PATH),
    )

    decision = evaluate_policy(req)
    write_audit(
        {
            "stage": "policy_decision",
            "request_id": req.request_id,
            "allowed": decision.allowed,
            "reason": decision.reason,
        },
        path=str(AUDIT_PATH),
    )
    if not decision.allowed:
        event("POLICY REJECTED", decision.reason)
        event("AUDIT EVENT CREATED", str(AUDIT_PATH))
        return None

    event("POLICY PASSED", decision.reason)
    token_info = issue_request_bound_token(req, ttl_seconds=ttl_seconds)
    write_audit(
        {
            "stage": "token_issued",
            "request_id": req.request_id,
            "expires_at": token_info["expires_at"],
        },
        path=str(AUDIT_PATH),
    )
    event("EXECUTION TOKEN ISSUED", token_summary(token_info))
    event("AUDIT EVENT CREATED", str(AUDIT_PATH))
    return token_info


def scenario_valid() -> None:
    banner("Scenario A — 정상 요청 / Valid request")
    req = ExecutionRequest(
        request_id="demo-valid-001",
        action="approve_transfer",
        target="wallet_A",
        amount=1000.0,
        requester="client_app",
    )
    token_info = relay_authorize(req)
    assert token_info is not None

    result = process_execution(request_to_dict(req), token_info["token"], audit_path=str(AUDIT_PATH))
    if result["status"] == "EXECUTED":
        event("ENDPOINT VERIFICATION SUCCESS")
        event("EXECUTION APPROVED", result["detail"])
        event("AUDIT EVENT CREATED", str(AUDIT_PATH))
    else:
        event("EXECUTION REJECTED", result["detail"])


def scenario_tampered_amount() -> None:
    banner("Scenario B-1 — 변조 요청 / Tampered amount")
    req = ExecutionRequest(
        request_id="demo-tamper-amount-001",
        action="approve_transfer",
        target="wallet_A",
        amount=1000.0,
        requester="client_app",
    )
    token_info = relay_authorize(req)
    assert token_info is not None

    tampered = request_to_dict(req)
    tampered["amount"] = 90000.0
    event("TAMPERED REQUEST DETECTED", "amount changed after token issuance")
    result = process_execution(tampered, token_info["token"], audit_path=str(AUDIT_PATH))
    event("ENDPOINT VERIFICATION FAILED", result["detail"])
    event("EXECUTION REJECTED", result["detail"])
    event("AUDIT EVENT CREATED", str(AUDIT_PATH))


def scenario_expired_token() -> None:
    banner("Scenario B-2 — 비정상 요청 / Expired token")
    req = ExecutionRequest(
        request_id="demo-expired-001",
        action="approve_transfer",
        target="wallet_A",
        amount=500.0,
        requester="client_app",
    )
    token_info = relay_authorize(req, ttl_seconds=-1)
    assert token_info is not None
    result = process_execution(request_to_dict(req), token_info["token"], audit_path=str(AUDIT_PATH))
    event("ENDPOINT VERIFICATION FAILED", result["detail"])
    event("EXECUTION REJECTED", result["detail"])
    event("AUDIT EVENT CREATED", str(AUDIT_PATH))


def print_audit_log() -> None:
    banner("Audit log output")
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))


def main() -> None:
    os.environ.setdefault("TOKEN_SECRET", "demo-secret-change-me-for-local-runs")
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text("", encoding="utf-8")

    print("Execution-Separated Custody MVP demo")
    print("Core message: application servers do not directly perform critical execution.")
    print("Flow: Client → Relay policy → execution token → Endpoint independent verification → execute/reject → audit log")

    scenario_valid()
    scenario_tampered_amount()
    scenario_expired_token()
    print_audit_log()


if __name__ == "__main__":
    main()
