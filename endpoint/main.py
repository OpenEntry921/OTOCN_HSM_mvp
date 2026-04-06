from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from endpoint.executor import execute_action
from endpoint.verifier import verify_token

app = FastAPI(title="Endpoint Server", version="0.1.0")


class ExecutePayload(BaseModel):
    request: dict
    execution_token: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "endpoint"}


@app.post("/execute")
def execute(payload: ExecutePayload):
    try:
        token_data = verify_token(payload.execution_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    req = payload.request

    for field in ("request_id", "action", "target", "requester"):
        if token_data.get(field) != req.get(field):
            raise HTTPException(status_code=400, detail=f"Token claim mismatch: {field}")

    return execute_action(
        action=req["action"],
        target=req["target"],
        request_id=req["request_id"],
    )
