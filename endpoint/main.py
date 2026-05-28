from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from endpoint.service import process_execution

app = FastAPI(title="Endpoint Server", version="0.1.0")


class ExecutePayload(BaseModel):
    request: dict
    execution_token: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "endpoint"}


@app.post("/execute")
def execute(payload: ExecutePayload):
    result = process_execution(payload.request, payload.execution_token)
    if result["status"] == "REJECTED":
        raise HTTPException(status_code=400, detail=result["detail"])
    return result
