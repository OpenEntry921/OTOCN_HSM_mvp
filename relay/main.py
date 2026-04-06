from fastapi import FastAPI, HTTPException
import requests

from shared.schemas import ExecutionRequest
from policy import evaluate_policy
from token_service import issue_token
from audit import write_audit

app = FastAPI(title="Relay Server")

ENDPOINT_URL = "http://endpoint:8001/execute"


@app.post("/request")
def handle_request(req: ExecutionRequest):
    decision = evaluate_policy(req)

    write_audit({
        "stage": "policy",
        "request_id": req.request_id,
        "allowed": decision.allowed,
        "reason": decision.reason
    })

    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)

    token_payload = {
        "request_id": req.request_id,
        "action": req.action,
        "target": req.target,
        "requester": req.requester
    }
    token_info = issue_token(token_payload)

    response = requests.post(
        ENDPOINT_URL,
        json={
            "request": req.dict(),
            "execution_token": token_info["token"]
        },
        timeout=5
    )

    write_audit({
        "stage": "forward",
        "request_id": req.request_id,
        "endpoint_status": response.status_code
    })

    return response.json()
