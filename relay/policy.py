from shared.schemas import ExecutionRequest, PolicyDecision


WHITELIST = {"wallet_A", "wallet_B"}
MAX_AMOUNT = 100000.0


def evaluate_policy(req: ExecutionRequest) -> PolicyDecision:
    if req.target not in WHITELIST:
        return PolicyDecision(allowed=False, reason="Target not whitelisted")

    if req.amount is not None and req.amount > MAX_AMOUNT:
        return PolicyDecision(allowed=False, reason="Amount exceeds limit")

    if req.action not in {"sign_tx", "approve_transfer"}:
        return PolicyDecision(allowed=False, reason="Unsupported action")

    return PolicyDecision(allowed=True, reason="Approved")
