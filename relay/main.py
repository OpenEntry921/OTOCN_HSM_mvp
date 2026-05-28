import os

import requests
from fastapi import FastAPI, HTTPException

from relay.audit import write_audit
from relay.policy import evaluate_policy
from relay.token_service import issue_token
from shared.schemas import ExecutionRequest

app = FastAPI(title="Relay Server", version="0.1.0")

ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://endpoint:8001/execute")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "relay"}


@app.post("/request")
def handle_request(req: ExecutionRequest):
    write_audit(
        {
            "stage": "request_received",
            "request_id": req.request_id,
            "action": req.action,
            "target": req.target,
            "requester": req.requester,
        }
    )

    decision = evaluate_policy(req)

    write_audit(
        {
            "stage": "policy_decision",
            "request_id": req.request_id,
            "allowed": decision.allowed,
            "reason": decision.reason,
        }
    )

    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    token_payload = {
        "request_id": req.request_id,
        "action": req.action,
        "target": req.target,
        "amount": req.amount,
        "requester": req.requester,
    }
    token_info = issue_token(token_payload)

    write_audit(
        {
            "stage": "token_issued",
            "request_id": req.request_id,
            "expires_at": token_info["expires_at"],
        }
    )

    try:
        response = requests.post(
            ENDPOINT_URL,
            json={
                "request": req.dict(),
                "execution_token": token_info["token"],
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        write_audit(
            {
                "stage": "forward_failed",
                "request_id": req.request_id,
                "error": str(exc),
            }
        )
        raise HTTPException(status_code=502, detail="Endpoint request failed") from exc

    write_audit(
        {
            "stage": "forward_success",
            "request_id": req.request_id,
            "endpoint_status": response.status_code,
        }
    )

    return response.json()
