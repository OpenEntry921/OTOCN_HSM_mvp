from pydantic import BaseModel
from typing import Optional
from time import time


class ExecutionRequest(BaseModel):
    request_id: str
    action: str
    target: str
    amount: Optional[float] = None
    requester: str
    timestamp: float = time()


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str


class ExecutionToken(BaseModel):
    token: str
    expires_at: float


class ExecutionResult(BaseModel):
    request_id: str
    status: str
    detail: str
