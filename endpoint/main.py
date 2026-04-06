from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from verifier import verify_token
from executor import execute_action

app = FastAPI(title="Endpoint Server")


class ExecutePayload(BaseModel):
    request: dict
    execution_token: str


@app.post("/execute")
def execute(payload: ExecutePayload):
    try:
        token_data = verify_token(payload.execution_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    req = payload.request

    if token_data["request_id"] != req["request_id"]:
        raise HTTPException(status_code=400, detail="Request ID mismatch")

    result = execute_action(
        action=req["action"],
        target=req["target"],
        request_id=req["request_id"]
    )
    return result
