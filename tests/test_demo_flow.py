import json

from endpoint.service import process_execution
from relay.audit import write_audit
from relay.policy import evaluate_policy
from relay.token_service import issue_token
from shared.schemas import ExecutionRequest


TOKEN_PAYLOAD = {
    "request_id": "req-001",
    "action": "sign_tx",
    "target": "wallet_A",
    "requester": "client_app",
}


def as_dict(req: ExecutionRequest) -> dict:
    if hasattr(req, "model_dump"):
        return req.model_dump()
    return req.dict()


def valid_request(request_id: str = "req-valid") -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id,
        action="approve_transfer",
        target="wallet_A",
        amount=1000.0,
        requester="client_app",
    )


def token_for(req: ExecutionRequest, ttl_seconds: int = 30) -> str:
    return issue_token(
        {
            "request_id": req.request_id,
            "action": req.action,
            "target": req.target,
            "amount": req.amount,
            "requester": req.requester,
        },
        ttl_seconds=ttl_seconds,
    )["token"]


def test_valid_request_should_pass_policy() -> None:
    decision = evaluate_policy(valid_request())

    assert decision.allowed is True
    assert decision.reason == "Approved"


def test_token_should_be_bound_to_original_request(tmp_path) -> None:
    req = valid_request("req-bound")
    token = token_for(req)

    result = process_execution(as_dict(req), token, audit_path=str(tmp_path / "audit.log"))

    assert result["status"] == "EXECUTED"


def test_tampered_amount_should_be_rejected(tmp_path) -> None:
    req = valid_request("req-tampered-amount")
    token = token_for(req)
    tampered = as_dict(req)
    tampered["amount"] = 90000.0

    result = process_execution(tampered, token, audit_path=str(tmp_path / "audit.log"))

    assert result["status"] == "REJECTED"
    assert result["detail"] == "Token claim mismatch: amount"


def test_tampered_destination_should_be_rejected(tmp_path) -> None:
    req = valid_request("req-tampered-destination")
    token = token_for(req)
    tampered = as_dict(req)
    tampered["target"] = "wallet_B"

    result = process_execution(tampered, token, audit_path=str(tmp_path / "audit.log"))

    assert result["status"] == "REJECTED"
    assert result["detail"] == "Token claim mismatch: target"


def test_expired_token_should_be_rejected(tmp_path) -> None:
    req = valid_request("req-expired")
    token = token_for(req, ttl_seconds=-1)

    result = process_execution(as_dict(req), token, audit_path=str(tmp_path / "audit.log"))

    assert result["status"] == "REJECTED"
    assert result["detail"] == "token expired"


def test_audit_event_should_be_created(tmp_path) -> None:
    audit_path = tmp_path / "audit.log"

    write_audit(
        {"stage": "test_event", "request_id": "req-audit", "status": "created"},
        path=str(audit_path),
    )

    content = audit_path.read_text(encoding="utf-8")
    assert '"stage": "test_event"' in content
    assert '"request_id": "req-audit"' in content


def test_token_issue_response_should_include_expiration_fields() -> None:
    req = valid_request("req-expiration-output")
    token_info = issue_token(
        {
            "request_id": req.request_id,
            "action": req.action,
            "target": req.target,
            "amount": req.amount,
            "requester": req.requester,
        }
    )

    assert "expires_at" in token_info
    assert "expires_at_iso" in token_info
    assert token_info["expires_at_iso"].endswith("Z")


def test_demo_token_issued_output_should_include_expiration_fields() -> None:
    from scripts.demo_flow import token_summary

    token_info = issue_token(TOKEN_PAYLOAD)
    summary = token_summary(token_info)

    assert "expires_at=" in summary
    assert "expires_at_iso=" in summary


def test_demo_token_issued_audit_event_should_include_expires_at_iso(
    tmp_path, monkeypatch
) -> None:
    from scripts import demo_flow

    audit_path = tmp_path / "audit.log"
    monkeypatch.setattr(demo_flow, "AUDIT_PATH", audit_path)

    token_info = demo_flow.relay_authorize(valid_request("req-audit-expiration"))

    assert token_info is not None
    records = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]
    token_issued = [record for record in records if record["stage"] == "token_issued"]
    assert token_issued[0]["expires_at"] == token_info["expires_at"]
    assert token_issued[0]["expires_at_iso"] == token_info["expires_at_iso"]
