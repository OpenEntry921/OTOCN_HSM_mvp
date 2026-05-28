from typing import Any, Dict, Optional

from endpoint.executor import execute_action
from endpoint.verifier import verify_token
from relay.audit import write_audit

BOUND_TOKEN_FIELDS = ("request_id", "action", "target", "amount", "requester")


def process_execution(
    request: Dict[str, Any],
    execution_token: str,
    audit_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify a request-bound execution token and simulate endpoint execution.

    The Endpoint does its own verification instead of trusting the Relay-forwarded
    request body. Any mismatch between token claims and request fields is rejected.
    """
    request_id = request.get("request_id", "unknown")

    try:
        token_data = verify_token(execution_token)
    except ValueError as exc:
        reason = str(exc)
        write_audit(
            {
                "stage": "endpoint_verification_failed",
                "request_id": request_id,
                "status": "rejected",
                "reason": reason,
            },
            path=audit_path,
        )
        return {
            "request_id": request_id,
            "status": "REJECTED",
            "detail": reason,
        }

    for field in BOUND_TOKEN_FIELDS:
        if token_data.get(field) != request.get(field):
            reason = f"Token claim mismatch: {field}"
            write_audit(
                {
                    "stage": "endpoint_verification_failed",
                    "request_id": request_id,
                    "status": "rejected",
                    "reason": reason,
                },
                path=audit_path,
            )
            return {
                "request_id": request_id,
                "status": "REJECTED",
                "detail": reason,
            }

    write_audit(
        {
            "stage": "endpoint_verification_success",
            "request_id": request_id,
            "status": "verified",
        },
        path=audit_path,
    )

    result = execute_action(
        action=request["action"],
        target=request["target"],
        request_id=request_id,
    )
    status = "EXECUTED" if result["status"] == "success" else "REJECTED"
    result = {**result, "status": status}

    write_audit(
        {
            "stage": "execution_result",
            "request_id": request_id,
            "status": result["status"],
            "detail": result["detail"],
        },
        path=audit_path,
    )
    return result
