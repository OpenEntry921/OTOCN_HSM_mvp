def execute_action(action: str, target: str, request_id: str) -> dict:
    if action == "sign_tx":
        return {
            "request_id": request_id,
            "status": "success",
            "detail": f"Simulated signing completed for {target}"
        }

    if action == "approve_transfer":
        return {
            "request_id": request_id,
            "status": "success",
            "detail": f"Simulated transfer approval completed for {target}"
        }

    return {
        "request_id": request_id,
        "status": "failed",
        "detail": "Unsupported action"
    }
