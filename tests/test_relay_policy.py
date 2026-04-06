from relay.policy import evaluate_policy
from shared.schemas import ExecutionRequest


def test_policy_allows_known_target() -> None:
    req = ExecutionRequest(
        request_id="req-001",
        action="sign_tx",
        target="wallet_A",
        requester="client_app",
    )
    decision = evaluate_policy(req)
    assert decision.allowed is True


def test_policy_denies_unknown_target() -> None:
    req = ExecutionRequest(
        request_id="req-002",
        action="sign_tx",
        target="wallet_Z",
        requester="client_app",
    )
    decision = evaluate_policy(req)
    assert decision.allowed is False
    assert decision.reason == "Target not whitelisted"
