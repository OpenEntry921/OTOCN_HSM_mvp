from time import time
from typing import Optional

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    request_id: str
    action: str
    target: str
    amount: Optional[float] = None
    requester: str
    timestamp: float = Field(default_factory=time)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str


class ExecutionToken(BaseModel):
    token: str
    expires_at: float
    expires_at_iso: str


class ExecutionResult(BaseModel):
    request_id: str
    status: str
    detail: str
